import logging
import requests
from ninja import Router
from .schema import SteamStatsInput, SteamStatsOutput
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

router = Router()

@router.get("/games/{steam_id}", response=dict)
def list_user_games(request, steam_id: str):
    cached_games = cache.get(f"games_{steam_id}")
    if cached_games:
        return {"games": cached_games}

    games = fetch_owned_games(steam_id)
    if games is None:
        return {"error": "Failed to fetch games or no games found."}

    cache.set(f"games_{steam_id}", games, timeout=3600)
    return {"games": games}

@router.post("/user-stats", response=SteamStatsOutput)
def get_user_stats(request, payload: SteamStatsInput):
    steam_id = payload.steam_id
    game_name = payload.game_name

    cached_games = cache.get(f"games_{steam_id}")
    if not cached_games:
        user_games = fetch_owned_games(steam_id)
        if user_games is None:
            return {"error": "Failed to fetch games or no games found."}
        cache.set(f"games_{steam_id}", user_games, timeout=3600)
    else:
        user_games = cached_games

    game_id = next((game["appid"] for game in user_games if game["name"].lower() == game_name.lower()), None)

    if not game_id:
        return {"error": "Game not found in user's library."}

    cached_stats = cache.get(f"stats_{steam_id}_{game_name}")
    if cached_stats:
        return cached_stats

    user_info_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
    user_info_params = {"key": settings.STEAM_API_KEY, "steamids": steam_id}
    try:
        user_info_resp = requests.get(user_info_url, params=user_info_params).json()
        user_data = user_info_resp.get("response", {}).get("players", [{}])[0]
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch user info: {e}")
        return {"error": "Failed to fetch user information from Steam."}

    stats_url = f"http://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/"
    stats_params = {"key": settings.STEAM_API_KEY, "steamid": steam_id, "appid": game_id}
    try:
        stats_resp = requests.get(stats_url, params=stats_params).json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game stats: {e}")
        return {"error": "Failed to fetch game stats from Steam."}

    logger.info(f"Stats Response for {game_name}: {stats_resp}")

    stats = [
        {"name": stat["name"], "value": str(stat["value"])}
        for stat in stats_resp.get("playerstats", {}).get("stats", [])
    ]

    result = {
        "steam_name": user_data.get("personaname", "Unknown User"),
        "game_time": user_data.get("playtime_forever", 0) / 60,
        "stats": stats
    }

    cache.set(f"stats_{steam_id}_{game_name}", result, timeout=3600)
    
    return result

def fetch_owned_games(steam_id):
    url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": settings.STEAM_API_KEY,
        "steamid": steam_id,
        "include_appinfo": True,
        "include_played_free_games": True,
        "format": "json"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        games = response.json().get("response", {}).get("games", [])
        return games
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch owned games: {e}")
        return None