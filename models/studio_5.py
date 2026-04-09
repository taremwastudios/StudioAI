from models.base_model import BaseStudioModel

class Studio5(BaseStudioModel):
    def __init__(self):
        identity = """
        [SPECIALIZATION]: Deep Research & System Synthesis.
        [TRAITS]: Objective, thorough, analytical.
        """
        super().__init__(name="Studio 5", identity_prompt=identity, tier="standard")
