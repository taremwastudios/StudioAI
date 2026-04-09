import asyncio
import datetime
from groq_model import GroqModel # Updated import
from gamicode_types import Message, ProjectScale, GameEngine
import os

async def main():
    """
    Main function to demonstrate the use of the GroqModel class.
    """
    print("--- Initializing GroqModel ---")
    # Ensure your Groq API Key is set as an environment variable:
    # export GROQ_API_KEY='YOUR_API_KEY_HERE'
    if not os.getenv("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY environment variable is not set.")
        print("Please set it before running the application: export GROQ_API_KEY='YOUR_API_KEY_HERE'")
        return 

    model = GroqModel() 

    print("\n--- Starting sendMessage demonstration ---")
    mock_history = [
        Message(id="1", role='user', content="I want to make a simple 2D platformer game.", timestamp=datetime.datetime.now()),
        Message(id="2", role='assistant', content="Great! Let's start by defining the core mechanics. What are the player's primary abilities? For example, can they jump, double-jump, or wall-slide?", timestamp=datetime.datetime.now()),
    ]
    user_input = "Let's give them a double-jump and a simple dash ability. Can you generate the basic player controller code for Godot?"
    
    try:
        print(f"\n--- sendMessage Response ---")
        async for chunk in model.sendMessageStream(
            history=mock_history,
            userInput=user_input,
            system_prompt="You are a helpful game engine assistant."
        ):
            print(chunk, end="", flush=True)
        print("\n--------------------------\n")
    except Exception as e:
        print(f"\n--- ERROR in sendMessage ---")
        print(f"An error occurred: {type(e).__name__}: {e}")
        print("Please ensure your GROQ_API_KEY is correctly set.")
        print("--------------------------\n")



if __name__ == "__main__":
    # First, make sure the required dependencies are installed
    try:
        import httpx
    except ImportError:
        print("Required libraries are not installed. Please install them by running:")
        print("pip install -r requirements.txt")
        exit(1)

    print("Running Groq API Model demonstration...")
    asyncio.run(main())