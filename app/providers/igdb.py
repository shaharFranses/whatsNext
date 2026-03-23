import httpx
import logging
from typing import Any, Dict, List, Optional
import time

logger = logging.getLogger(__name__)

IGDB_AUTH_URL = "https://id.twitch.tv/oauth2/token"
IGDB_API_BASE = "https://api.igdb.com/v4"

# Image URL template — replace {image_id} and optionally {size}
# Sizes: cover_small (90x128), cover_big (264x374), 720p, 1080p
IGDB_IMAGE_URL = "https://images.igdb.com/igdb/image/upload/t_{size}/{image_id}.jpg"


class IGDBProvider:
    """Wraps the IGDB API v4 for game metadata and recommendations."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        mock: bool = False,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.mock = mock or not (client_id and client_secret)
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0

        # Caches: populated on first use, reused for the session
        self._genre_cache: Dict[str, int] = {}   # name -> id
        self._theme_cache: Dict[str, int] = {}   # name -> id

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def _authenticate(self) -> str:
        """Fetch / reuse an OAuth2 token from Twitch."""
        if self._access_token and time.time() < self._token_expiry - 60:
            return self._access_token

        if not (self.client_id and self.client_secret):
            raise RuntimeError("Missing Client ID or Secret for IGDB authentication")

        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(IGDB_AUTH_URL, params=params, timeout=15.0)
            response.raise_for_status()
            data = response.json()

        self._access_token = data.get("access_token")
        if not self._access_token:
            raise RuntimeError("Failed to retrieve access token from IGDB")

        self._token_expiry = time.time() + data.get("expires_in", 3600)
        logger.info("IGDB OAuth token acquired (expires in %ss)", data.get("expires_in"))
        return self._access_token

    # ------------------------------------------------------------------
    # Low-level POST helper
    # ------------------------------------------------------------------

    async def _post(self, endpoint: str, query: str) -> List[Dict[str, Any]]:
        """Send an Apicalypse query to an IGDB endpoint. Returns the JSON list."""
        token = await self._authenticate()
        url = f"{IGDB_API_BASE}/{endpoint}"
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/plain",
        }

        async with httpx.AsyncClient() as client:
            for attempt in range(3):
                try:
                    response = await client.post(
                        url, headers=headers, content=query, timeout=30.0
                    )
                    if response.status_code == 429:
                        wait = int(response.headers.get("Retry-After", "2"))
                        logger.warning("IGDB rate-limited, waiting %ss…", wait)
                        await _async_sleep(wait)
                        continue
                    response.raise_for_status()
                    data = response.json()
                    return data if isinstance(data, list) else []
                except httpx.TimeoutException:
                    logger.warning("IGDB timeout on attempt %d/3", attempt + 1)
                    if attempt == 2:
                        raise

        return []

    # ------------------------------------------------------------------
    # Genre / Theme ID resolution (cached)
    # ------------------------------------------------------------------

    async def _load_genre_cache(self) -> None:
        """Fetch ALL genres from IGDB and cache name→id."""
        if self._genre_cache:
            return
        results = await self._post("genres", "fields id, name; limit 500;")
        for g in results:
            name = g.get("name", "")
            gid = g.get("id")
            if name and gid:
                self._genre_cache[name.lower()] = gid
        logger.info("Cached %d IGDB genres", len(self._genre_cache))

    async def _load_theme_cache(self) -> None:
        """Fetch ALL themes from IGDB and cache name→id."""
        if self._theme_cache:
            return
        results = await self._post("themes", "fields id, name; limit 500;")
        for t in results:
            name = t.get("name", "")
            tid = t.get("id")
            if name and tid:
                self._theme_cache[name.lower()] = tid
        logger.info("Cached %d IGDB themes", len(self._theme_cache))

    async def resolve_genre_ids(self, names: List[str]) -> List[int]:
        """Convert genre name strings to IGDB genre IDs."""
        await self._load_genre_cache()
        ids = []
        for n in names:
            gid = self._genre_cache.get(n.lower())
            if gid:
                ids.append(gid)
        return ids

    async def resolve_theme_ids(self, names: List[str]) -> List[int]:
        """Convert theme name strings to IGDB theme IDs."""
        await self._load_theme_cache()
        ids = []
        for n in names:
            tid = self._theme_cache.get(n.lower())
            if tid:
                ids.append(tid)
        return ids

    # ------------------------------------------------------------------
    # Cover URL construction
    # ------------------------------------------------------------------

    @staticmethod
    def build_cover_url(image_id: str, size: str = "cover_big") -> str:
        """Build a full IGDB image URL from an image_id.

        Common sizes: cover_small, cover_big, 720p, 1080p
        """
        return IGDB_IMAGE_URL.format(image_id=image_id, size=size)

    @staticmethod
    def extract_cover_url(game: Dict[str, Any]) -> str:
        """Extract or build a cover URL from a game dict returned by IGDB."""
        cover = game.get("cover")
        if isinstance(cover, dict):
            image_id = cover.get("image_id")
            if image_id:
                return IGDBProvider.build_cover_url(image_id)
            # Fallback: some responses include a url field
            url = cover.get("url", "")
            if url:
                # IGDB returns protocol-relative URLs like //images.igdb.com/…
                return url if url.startswith("http") else f"https:{url}"
        return "https://via.placeholder.com/264x352?text=No+Cover"

    # ------------------------------------------------------------------
    # Game search
    # ------------------------------------------------------------------

    async def search_game(self, name: str) -> List[Dict[str, Any]]:
        """Search for a game by name. Returns a list with the best match."""
        query = (
            f'search "{name}";'
            " fields name, genres.name, themes.name, keywords.name,"
            " summary, cover.image_id, total_rating;"
            " limit 1;"
        )
        results = await self._post("games", query)

        # Attach a full cover_url for convenience
        for game in results:
            game["cover_url"] = self.extract_cover_url(game)

        return results

    async def get_game_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Fetch metadata for a specific game by name."""
        results = await self.search_game(name)
        if not results:
            return None
        return results[0]

    # ------------------------------------------------------------------
    # Batch tag fetching (used by TagAggregator)
    # ------------------------------------------------------------------

    async def get_tags_for_games(self, names: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """Batch-fetch tags (genres + themes + keywords) for game names separately."""
        tags_map: Dict[str, Dict[str, List[str]]] = {}
        for name in names:
            metadata = await self.get_game_metadata(name)
            if metadata:
                game_tags: Dict[str, List[str]] = {}
                for field in ["genres", "themes", "keywords"]:
                    items = metadata.get(field, [])
                    if isinstance(items, list):
                        game_tags[field] = [
                            item["name"] for item in items 
                            if isinstance(item, dict) and "name" in item
                        ]
                    else:
                        game_tags[field] = []
                tags_map[name] = game_tags
            else:
                tags_map[name] = {"genres": [], "themes": [], "keywords": []}
        return tags_map

    # ------------------------------------------------------------------
    # Recommendation queries (called by Recommender)
    # ------------------------------------------------------------------

    async def query_games(
        self,
        *,
        genre_ids: Optional[List[int]] = None,
        theme_ids: Optional[List[int]] = None,
        min_rating: float = 75,
        min_rating_count: Optional[int] = None,
        max_rating_count: Optional[int] = None,
        released_before: Optional[int] = None,
        released_after: Optional[int] = None,
        exclude_names: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Flexible game query builder.

        All filters are optional; only set ones are included in the where clause.
        Returns games sorted by total_rating descending.
        """
        fields = (
            "fields name, summary, genres.name, themes.name, keywords.name,"
            " total_rating, total_rating_count, cover.image_id,"
            " first_release_date;"
        )

        conditions = [
            "parent_game = null",  # Exclude DLCs/expansions
            f"total_rating >= {min_rating}",
        ]

        if genre_ids:
            ids_str = ",".join(str(i) for i in genre_ids)
            conditions.append(f"genres = ({ids_str})")

        if theme_ids:
            ids_str = ",".join(str(i) for i in theme_ids)
            conditions.append(f"themes = ({ids_str})")

        if min_rating_count is not None:
            conditions.append(f"total_rating_count >= {min_rating_count}")

        if max_rating_count is not None:
            conditions.append(f"total_rating_count < {max_rating_count}")

        if released_before is not None:
            conditions.append(f"first_release_date < {released_before}")

        if released_after is not None:
            conditions.append(f"first_release_date > {released_after}")

        where = " & ".join(conditions)
        query = f"{fields} where {where}; sort total_rating desc; limit {limit};"

        results = await self._post("games", query)

        # Enrich each result with a usable cover_url
        for game in results:
            game["cover_url"] = self.extract_cover_url(game)

        # Optionally filter out games the user already owns
        if exclude_names:
            exclude_lower = {n.lower() for n in exclude_names}
            results = [
                g for g in results
                if g.get("name", "").lower() not in exclude_lower
            ]

        return results


# ------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------

async def _async_sleep(seconds: int) -> None:
    """Async sleep helper for rate-limit back-off."""
    import asyncio
    await asyncio.sleep(seconds)
