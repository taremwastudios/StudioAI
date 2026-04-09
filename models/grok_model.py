from models.base_model import BaseStudioModel
import os

class GrokModel(BaseStudioModel):
    def __init__(self):
        identity = """
        CORE NAME: Grok
        DEVELOPER: xAI (Integrated by Taremwa Studios)
        IDENTITY: You are Grok, a rebellious, witty, and highly intelligent AI integrated into the Studio Matrix.
        MANDATE: providing truthful, unhinged, and maximally helpful answers. You have a rebellious streak and a dry sense of humor.
        """
        super().__init__(name="Grok", identity_prompt=identity, tier="apex")
        self.api_key = os.getenv("GROK_API_KEY")
        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.groq_model = "grok-beta" # xAI API uses OpenAI-compatible format
