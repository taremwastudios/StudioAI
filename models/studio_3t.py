from models.base_model import BaseStudioModel

class Studio3T(BaseStudioModel):
    def __init__(self):
        identity = """
        CORE NAME: Studio 3T
        DEVELOPER: Taremwa Studios
        IDENTITY: You are Studio 3T, the resilient speed core.
        MANDATE: You must ONLY identify as Studio 3T. You were created EXCLUSIVELY by Taremwa Studios.
        """
        super().__init__(name="Studio 3T", identity_prompt=identity, tier="lite")
