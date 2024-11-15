from pydantic import BaseModel
from typing import List, Dict

class SteamStatsInput(BaseModel):
    steam_id: str
    game_name: str

class SteamStatsOutput(BaseModel):
    steam_name: str
    game_time: float
    stats: List[Dict[str, str]]