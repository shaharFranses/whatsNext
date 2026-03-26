import asyncio
import httpx
from typing import Any, Dict, List, Optional

STEAM_API_BASE = "https://api.steampowered.com"


class SteamProvider:
    """Wraps the Steam Web API for player game data."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=15.0)

    async def get_owned_games(self, steam_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all games owned by the given Steam user.
        Returns a list of dicts with keys: appid, name, playtime_forever, etc.
        """
        url = f"{STEAM_API_BASE}/IPlayerService/GetOwnedGames/v1/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "include_appinfo": True,
            "include_played_free_games": True,
            "format": "json",
        }

        response = await self._client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        games = data.get("response", {}).get("games", [])
        return games

    async def get_top_games(self, steam_id: str, n: int = 5) -> List[Dict[str, Any]]:
        """Return the top-n games sorted by playtime (descending)."""
        games = await self.get_owned_games(steam_id)
        sorted_games: List[Dict[str, Any]] = sorted(
            games, key=lambda g: g.get("playtime_forever", 0), reverse=True
        )
        return [sorted_games[i] for i in range(min(len(sorted_games), n))]

    async def get_player_achievements(self, steam_id: str, app_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch achievement stats for a single game.
        Returns {"achieved": int, "total": int, "completion_pct": float}
        or None if the game has no achievements / is unavailable.
        """
        url = f"{STEAM_API_BASE}/ISteamUserStats/GetPlayerAchievements/v1/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "appid": app_id,
            "l": "english",
        }

        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            player_stats = data.get("playerstats", {})

            # Error responses have {"success": false, "error": "..."}
            if player_stats.get("success") is False:
                return None

            achievements = player_stats.get("achievements", [])
            if not achievements:
                return None

            total = len(achievements)
            achieved = sum(1 for a in achievements if a.get("achieved") == 1)
            raw_pct: float = (achieved / total) * 100.0 if total > 0 else 0.0
            pct: float = round(raw_pct, 1)

            return {"achieved": achieved, "total": total, "completion_pct": pct}

        except (httpx.HTTPStatusError, httpx.RequestError):
            # Game may not have achievements or API may reject the request
            return None

    async def get_top_games_with_achievements(
        self, steam_id: str, n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Return top-n games sorted by *Achievement Completion Percentage*.
        Hybrid Approach:
        1. Fetch all games, filter out those with < 2 hours playtime.
        2. Take the Top 20 by playtime.
        3. Fetch achievements concurrently.
        4. Sort remaining by achievement completion %, return top n.
        """
        all_games = await self.get_owned_games(steam_id)

        # 1. Filter out < 2 hours (120 minutes)
        valid_games = [g for g in all_games if g.get("playtime_forever", 0) >= 120]

        # 2. Sort by playtime and take top 20
        top_by_playtime = sorted(
            valid_games, key=lambda g: g.get("playtime_forever", 0), reverse=True
        )[:20]

        if not top_by_playtime:
            return []

        # 3. Fetch achievements concurrently
        async def fetch_achievements_for_game(game: Dict[str, Any]) -> Dict[str, Any]:
            app_id = game["appid"]
            ach_data = await self.get_player_achievements(steam_id, app_id)
            name = game.get("name", f"AppID {app_id}")
            hours = round(game.get("playtime_forever", 0) / 60, 1)

            pct = 0.0
            if ach_data and "completion_pct" in ach_data:
                pct = ach_data["completion_pct"]

            return {
                "appid": app_id,
                "name": name,
                "playtime_hours": hours,
                "achievements": ach_data,
                "_sort_pct": pct,  # Internal sort key
            }

        tasks = [fetch_achievements_for_game(g) for g in top_by_playtime]
        results_tuple = await asyncio.gather(*tasks, return_exceptions=True)
        results = [r for r in results_tuple if not isinstance(r, Exception)]

        # 4. Sort by achievement percentage descending, then fallback to playtime
        results.sort(key=lambda x: (x["_sort_pct"], x["playtime_hours"]), reverse=True)

        # Remove internal sort key
        for r in results:
            r.pop("_sort_pct", None)

        return results[:n]
