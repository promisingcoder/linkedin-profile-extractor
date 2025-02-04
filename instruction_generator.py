from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
from openai import OpenAI
import json
import os
import logging
import time
from tenacity import retry, wait_random_exponential, stop_after_attempt

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class HTMLState(BaseModel):
    html: str
    description: str
    action_description: Optional[str] = None
    selector_to_click: Optional[str] = None

class ScrapingSequence(BaseModel):
    states: List[HTMLState]
    desired_data: Optional[str] = None
    urls_file: Optional[str] = None

class ScrapingInstruction(BaseModel):
    command: str
    args: Optional[str] = None
    description: str = ""  # Make description optional with default empty string

class InstructionSchema(BaseModel):
    instructions: List[Dict[str, Union[str, None]]]

class InstructionGenerator:
    def __init__(self, api_key=None):
        """Initialize the instruction generator with OpenAI API key."""
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
    def generate_instructions(self, sequence: ScrapingSequence) -> List[ScrapingInstruction]:
        """Generate scraping instructions by analyzing the sequence of HTML states."""
        system_prompt = """
        You are an expert at generating web scraping instructions. Your task is to analyze a sequence of HTML states and:
        1. Identify relevant elements and their XPath selectors
        2. Create appropriate scraping commands for each state
        3. Generate a complete instruction file that handles the entire sequence

        Return a JSON object with an 'instructions' array, where each instruction has:
        - command: the command name (string)
        - args: the command arguments (string or null). For EXTRACT commands, the args should be a JSON-encoded string of field:selector pairs
        - description: what this command does (string)

        Available commands:
        - FOR_EACH_URL (must be first command, reads URLs from a file)
        - VISIT_URL (visits the current URL from the file)
        - WAIT
        - WAIT_FOR
        - WAIT_RANDOM
        - CLICK_ELEMENT_BY_SELECTOR
        - EXTRACT (use with JSON object of field:selector pairs)
        - SAVE_TO (must be before END_FOR)
        - END_FOR (must be last command)

        For EXTRACT commands, analyze the HTML and determine the correct XPath selectors for each field.
        For CLICK commands, use the provided selector or determine the correct one from the HTML.
        For WAIT_FOR commands, determine what element should be waited for.

        IMPORTANT: 
        1. All args must be valid JSON strings. For EXTRACT commands, convert the selector object to a JSON string.
        2. The instruction sequence must start with FOR_EACH_URL and end with END_FOR
        3. SAVE_TO must be included before END_FOR to save the extracted data

        Example:
        {
            "instructions": [
                {
                    "command": "FOR_EACH_URL IN ",
                    "args": "urls.txt",
                    "description": "Process each URL from the file"
                },
                {
                    "command": "VISIT_URL",
                    "args": null,
                    "description": "Visit the current URL"
                },
                {
                    "command": "EXTRACT",
                    "args": "{\\"name\\": \\"//h1[@class='title']\\"}", 
                    "description": "Extract the name"
                },
                {
                    "command": "SAVE_TO",
                    "args": "output.json",
                    "description": "Save extracted data"
                },
                {
                    "command": "END_FOR",
                    "args": null,
                    "description": "End URL processing"
                }
            ]
        }
        """

        # Build the sequence description for the prompt
        sequence_description = "Sequence of HTML states and actions:\n\n"
        for i, state in enumerate(sequence.states):
            sequence_description += f"State {i + 1}:\n"
            sequence_description += f"Description: {state.description}\n"
            sequence_description += f"HTML Content:\n{state.html}\n\n"
            
            if state.action_description and state.selector_to_click:
                sequence_description += f"Action after this state:\n"
                sequence_description += f"Description: {state.action_description}\n"
                sequence_description += f"Selector to click: {state.selector_to_click}\n\n"

        user_prompt = f"""
        Analyze this sequence of HTML states and generate appropriate scraping instructions:

        URLs file: {sequence.urls_file or "urls.txt"}
        Desired data to extract: {sequence.desired_data if sequence.desired_data else "All relevant data"}

        {sequence_description}

        Requirements:
        1. Start with FOR_EACH_URL command using the URLs file
        2. Include VISIT_URL command after FOR_EACH_URL
        3. Generate instructions that handle the complete sequence
        4. Extract data at appropriate points in the sequence
        5. Include proper waiting times between actions
        6. Use the provided selectors for clicks when available
        7. Generate appropriate selectors for extractions
        8. Handle any dynamic content appropriately
        9. Ensure all selectors are specific and robust
        10. Include SAVE_TO command before END_FOR
        11. End with END_FOR command
        12. IMPORTANT: For EXTRACT commands, ensure the args is a valid JSON string
        """

        try:
            completion = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            # Parse the AI response
            response_content = completion.choices[0].message.content
            response = json.loads(response_content)
            
            # Validate response against schema
            validated_response = InstructionSchema(**response)
            
            # Convert to ScrapingInstruction objects
            instructions = []
            for instr in validated_response.instructions:
                # Ensure args is a JSON string if it's a dict
                if isinstance(instr.get('args'), dict):
                    instr['args'] = json.dumps(instr['args'])
                # If args is already a string but contains unescaped quotes, fix it
                elif isinstance(instr.get('args'), str):
                    try:
                        # Try to parse it as JSON first
                        json.loads(instr['args'])
                    except json.JSONDecodeError:
                        # If it fails, it might be a malformed JSON string, try to fix it
                        try:
                            # Parse it as a Python literal and convert to proper JSON
                            import ast
                            parsed = ast.literal_eval(instr['args'])
                            instr['args'] = json.dumps(parsed)
                        except:
                            # If all else fails, leave it as is
                            pass
                
                # Ensure description exists
                if 'description' not in instr:
                    instr['description'] = ""
                
                instructions.append(ScrapingInstruction(**instr))
            
            return instructions

        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON response: {e}")
            raise
        except Exception as e:
            logging.error(f"Error generating instructions: {e}")
            raise

    def save_instructions(self, instructions: List[ScrapingInstruction], output_file: str):
        """Save the instructions to a file."""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{output_file}_{timestamp}.txt"

            with open(filename, 'w') as f:
                # Write fields to be extracted as comments at the top
                fields = set()
                for instruction in instructions:
                    if instruction.command == "EXTRACT" and instruction.args:
                        try:
                            selectors = json.loads(instruction.args)
                            fields.update(selectors.keys())
                        except json.JSONDecodeError:
                            continue

                if fields:
                    f.write("# Fields to be extracted:\n")
                    for field in sorted(fields):
                        f.write(f"# - {field}\n")
                    f.write("\n")

                # Write instructions
                for instruction in instructions:
                    if instruction.args:
                        f.write(f"{instruction.command} {instruction.args}\n")
                    else:
                        f.write(f"{instruction.command}\n")

            logging.info(f"Instructions saved to {filename}")
            return filename

        except Exception as e:
            logging.error(f"Error saving instructions: {e}")
            raise

def read_html_file(path: str) -> str:
    """Read HTML content from a file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error reading HTML file: {e}")
        raise

def test_linkedin_profile_extraction():
    """Test function to demonstrate LinkedIn profile extraction sequence."""
    try:
        # Initialize generator
        generator = InstructionGenerator()

        # Define the scraping sequence
        states = [
            # State 1: Initial profile page
            HTMLState(
                html=read_html_file('test_data/initial_profile.html'),
                description="Initial LinkedIn profile page showing basic information",
                action_description="Click on Contact info button",
                selector_to_click="//a[@id='top-card-text-details-contact-info']"
            ),
            
            # State 2: Contact info button
            HTMLState(
                html=read_html_file('test_data/button.html'),
                description="Contact info button element",
                action_description="Wait for contact info dialog",
                selector_to_click=None
            ),
            
            # State 3: Contact info dialog
            HTMLState(
                html=read_html_file('test_data/contact_info.html'),
                description="Contact info dialog showing profile URL and websites",
                action_description=None,
                selector_to_click=None
            )
        ]

        # Create sequence with desired data
        sequence = ScrapingSequence(
            states=states,
            desired_data="""
            - Full name
            - Profile title
            - Location
            - Company
            - LinkedIn profile URL
            - Portfolio website
            - Company website
            """,
            urls_file="linkedin_profile_urls.txt"  # Specify the URLs file
        )

        # Generate instructions
        instructions = generator.generate_instructions(sequence)
        
        # Save instructions
        output_file = generator.save_instructions(instructions, 'linkedin_profile_instructions')
        
        logging.info(f"Test completed successfully. Instructions saved to: {output_file}")
        return output_file

    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        raise

def main():
    """Main function to run the instruction generator."""
    try:
        # Get API key from user if not set in environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            api_key = input("Please enter your OpenAI API key: ")
            os.environ['OPENAI_API_KEY'] = api_key

        # Ask if user wants to run the test or input custom sequence
        choice = input("Enter 'test' to run LinkedIn profile test or 'custom' for custom sequence: ").lower()
        
        if choice == 'test':
            test_linkedin_profile_extraction()
            return

        # Initialize generator
        generator = InstructionGenerator(api_key)

        # Get output file base name
        output_file = input("Enter base name for the instructions file: ")

        # Initialize sequence
        states = []
        urls_file = input("Enter the URLs file name (e.g., urls.txt): ")
        desired_data = input("Enter desired data to extract (or press Enter for all): ") or None

        while True:
            print("\n=== Adding New State ===")
            # Get HTML content
            html_path = input("Enter path to HTML file (or 'done' to finish): ")
            if html_path.lower() == 'done':
                break

            html_content = read_html_file(html_path)
            description = input("Enter description for this state: ")

            # Ask about actions after this state
            has_action = input("Is there an action after this state? (y/n): ").lower() == 'y'
            action_description = None
            selector_to_click = None
            
            if has_action:
                action_description = input("Enter action description: ")
                selector_to_click = input("Enter selector to click (XPath or CSS): ")

            # Create and add the state
            state = HTMLState(
                html=html_content,
                description=description,
                action_description=action_description,
                selector_to_click=selector_to_click
            )
            states.append(state)

            print(f"\nAdded state {len(states)} successfully!")

        if not states:
            print("No states added. Exiting.")
            return

        # Create sequence object
        sequence = ScrapingSequence(
            states=states,
            desired_data=desired_data,
            urls_file=urls_file
        )

        # Generate and save instructions
        instructions = generator.generate_instructions(sequence)
        generator.save_instructions(instructions, output_file)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main() 