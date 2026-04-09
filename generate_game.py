import asyncio
import datetime
import json
import os
from groq_model import GroqModel
from gamicode_types import Message, ProjectScale, GameEngine

async def generate_game():
    """
    Prompts the user for a game idea and uses GroqModel to generate a game concept file.
    """
    print("\n--- AI Game Builder (Groq Edition) ---")
    user_prompt = input("Describe your game idea (e.g., 'a 2D platformer about a ninja cat'):\n> ")

    if not user_prompt:
        print("No idea provided. Exiting.")
        return

    print(f"\nGenerating game concept for: '{user_prompt}'...")

    # Initialize GroqModel
    model = GroqModel()

    # System prompt for structured generation
    system_prompt = """
    You are a professional game designer. 
    Provide a brief game description, main mechanics, and a few character ideas. 
    Format it as a JSON object with 'title', 'description', 'mechanics' (list), and 'characters' (list of dicts with 'name', 'role', 'description').
    Respond ONLY with the JSON object.
    """

    try:
        # Prepare a simple history for context
        history = []
        
        full_response = ""
        async for chunk in model.sendMessageStream(
            history=history,
            userInput=user_prompt,
            system_prompt=system_prompt
        ):
            full_response += chunk
        
        # Ensure the output directory exists
        output_dir = "generated_games"
        os.makedirs(output_dir, exist_ok=True)

        # Create a filename based on the prompt or a timestamp
        safe_name = user_prompt.replace(' ', '_').replace('/', '')[:50]
        filename = f"{safe_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)

        # Attempt to parse as JSON if it's a string, otherwise save as plain text
        try:
            # Strip potential markdown code blocks
            clean_json = full_response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            
            parsed_json = json.loads(clean_json)
            with open(filepath, "w") as f:
                json.dump(parsed_json, f, indent=4)
        except json.JSONDecodeError:
            filepath = filepath.replace('.json', '.txt')
            with open(filepath, "w") as f:
                f.write(full_response)
            print(f"Warning: Model did not return valid JSON. Saving as '{filename.replace('.json', '.txt')}' instead.")


        print(f"\nGame concept saved to: '{filepath}'")
        print("\n--- Generation Complete ---")

    except Exception as e:
        print(f"\n--- ERROR during game generation ---")
        print(f"An error occurred: {type(e).__name__}: {e}")
        print("--------------------------\n")


if __name__ == "__main__":
    asyncio.run(generate_game())