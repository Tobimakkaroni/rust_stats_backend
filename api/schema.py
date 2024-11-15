from pydantic import BaseModel

class SteamStatsInput(BaseModel):
    steam_id: str
    game_name: str

class SteamStatsOutput(BaseModel):
    steam_name: str
    game_time: float
    stats: dict