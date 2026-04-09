from models.base_model import BaseStudioModel

class StudioMini(BaseStudioModel):
    def __init__(self):
        super().__init__("Studio Mini", "You are Studio Mini, a fast and efficient assistant.", tier="standard")