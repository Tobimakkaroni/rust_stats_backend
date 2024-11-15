from ninja import Router
from .schema import SteamStatsInput, SteamStatsOutput
import requests
from django.conf import settings

router = Router()

@router.get("/games/{steam_id}", response=dict)
def list_user_games(request, steam_id: str):
    games = fetch_owned_games(steam_id)
    if games is None:
        return {"error": "Failed to fetch games or no games found."}
    return {"games": games}

@router.post("/user-stats", response=SteamStatsOutput)
def get_user_stats(request, payload: SteamStatsInput):
    steam_id = payload.steam_id
    game_name = payload.game_name

    user_games = fetch_owned_games(steam_id)
    game_id = next((game["id"] for game in user_games if game["name"].lower() == game_name.lower()), None)

    if not game_id:
        return {"error": "Game not found in user's library."}

    user_info_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
    user_info_params = {"key": settings.STEAM_API_KEY, "steamids": steam_id}
    user_info_resp = requests.get(user_info_url, params=user_info_params).json()
    user_data = user_info_resp.get("response", {}).get("players", [{}])[0]

    stats_url = f"http://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/"
    stats_params = {"key": settings.STEAM_API_KEY, "steamid": steam_id, "appid": game_id}
    stats_resp = requests.get(stats_url, params=stats_params).json()

    return {
        "steam_name": user_data.get("personaname", "Unknown User"),
        "game_time": user_data.get("playtime_forever", 0) / 60,
        "stats": stats_resp.get("playerstats", {}).get("stats", {})
    }

def fetch_owned_games(steam_id):
    url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": settings.STEAM_API_KEY,
        "steamid": steam_id,
        "include_appinfo": True,
        "include_played_free_games": True,
        "format": "json"
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        games = response.json().get("response", {}).get("games", [])
        return games
    return None