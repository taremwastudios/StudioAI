
import httpx
import os

CLOUD_API = "http://127.0.0.1:8002"

class UserService:
    @staticmethod
    async def get_user_plan(player_name: str) -> str:
        """
        Queries the Taremwa Cloud API to determine if a user has a Taremwa ID.
        Returns 'Smart' if registered, 'Free' otherwise.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{CLOUD_API}/user/{player_name}")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("taremwa_id"):
                        return "Smart"
        except Exception as e:
            print(f"Cloud API unreachable: {e}")
        
        return "Free"
