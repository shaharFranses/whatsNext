import logging
from typing import Any, Dict, List
from app.providers.igdb import IGDBProvider

logger = logging.getLogger(__name__)


class Recommender:
    """Generates game recommendations based on user DNA and archetypes."""

    # Epoch timestamps for era boundaries
    CLASSIC_CUTOFF = 1262304000   # 2010-01-01
    MODERN_AFTER   = 1514764800   # 2018-01-01

    def __init__(self, igdb_provider: IGDBProvider):
        self.igdb = igdb_provider

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    async def _resolve_dna_genre_ids(self, dna: Dict[str, Any]) -> List[int]:
        """Turn the user's top_tags into IGDB genre IDs (best-effort)."""
        tags = dna.get("top_tags", [])
        ids = await self.igdb.resolve_genre_ids(tags)
        if not ids:
            # Fallback: try themes
            ids = await self.igdb.resolve_theme_ids(tags)
        return ids

    @staticmethod
    def _enrich(games: List[Dict[str, Any]], dna: Dict[str, Any], archetype: str) -> List[Dict[str, Any]]:
        """Add reasoning text and normalise fields for the frontend."""
        top_tags = set(dna.get("top_tags", []))
        enriched = []
        for game in games:
            game_tags = set()
            for field in ("genres", "themes", "keywords"):
                items = game.get(field, [])
                if isinstance(items, list):
                    game_tags.update(
                        item["name"] for item in items
                        if isinstance(item, dict) and "name" in item
                    )

            matching = list(top_tags & game_tags)

            if archetype == "modern":
                reasoning = (
                    f"Because you love {', '.join(matching[:2])}, this modern hit is a must-play."
                    if matching
                    else "A top-rated modern title that fits your library's vibe."
                )
            elif archetype == "gem":
                tag = matching[0] if matching else (list(top_tags)[0] if top_tags else "gaming")
                reasoning = f"A hidden gem with depth in {tag} — most players haven't found it yet."
            elif archetype == "indie":
                tag = matching[0] if matching else (list(top_tags)[0] if top_tags else "gaming")
                reasoning = f"An indie darling that nails the {tag} experience in a fresh way."
            elif archetype == "ancestry":
                tag = matching[0] if matching else (list(top_tags)[0] if top_tags else "this genre")
                reasoning = f"This classic laid the groundwork for the {tag} games you enjoy today."
            else:
                reasoning = "We think you'll enjoy this one."

            enriched.append({
                "name": game.get("name", "Unknown"),
                "summary": game.get("summary", "No summary available."),
                "cover_url": game.get("cover_url", "https://via.placeholder.com/264x352?text=No+Cover"),
                "total_rating": game.get("total_rating"),
                "reasoning": reasoning,
            })
        return enriched

    # ------------------------------------------------------------------
    # Archetype recommenders
    # ------------------------------------------------------------------

    async def recommend_modern(
        self, dna: Dict[str, Any], *, exclude: List[str] | None = None
    ) -> List[Dict[str, Any]]:
        """High-hype modern games matching user DNA."""
        genre_ids = await self._resolve_dna_genre_ids(dna)
        results = await self.igdb.query_games(
            genre_ids=genre_ids or None,
            min_rating=80,
            min_rating_count=50,
            released_after=self.MODERN_AFTER,
            exclude_names=exclude,
            limit=3,
        )
        return self._enrich(results, dna, "modern")

    async def recommend_hidden_gem(
        self, dna: Dict[str, Any], *, exclude: List[str] | None = None
    ) -> List[Dict[str, Any]]:
        """High-rated but low-popularity games."""
        genre_ids = await self._resolve_dna_genre_ids(dna)
        results = await self.igdb.query_games(
            genre_ids=genre_ids or None,
            min_rating=80,
            max_rating_count=20,
            exclude_names=exclude,
            limit=3,
        )
        return self._enrich(results, dna, "gem")

    async def recommend_indie(
        self, dna: Dict[str, Any], *, exclude: List[str] | None = None
    ) -> List[Dict[str, Any]]:
        """Indie-tagged games with matching DNA."""
        # "Indie" is a theme in IGDB (theme id will be resolved)
        indie_ids = await self.igdb.resolve_theme_ids(["Indie"])
        genre_ids = await self._resolve_dna_genre_ids(dna)
        results = await self.igdb.query_games(
            genre_ids=genre_ids or None,
            theme_ids=indie_ids or None,
            min_rating=75,
            min_rating_count=10,
            exclude_names=exclude,
            limit=3,
        )
        return self._enrich(results, dna, "indie")

    async def recommend_ancestry(
        self, dna: Dict[str, Any], *, exclude: List[str] | None = None
    ) -> List[Dict[str, Any]]:
        """Old Masterpieces: pre-2010 classics matching DNA."""
        genre_ids = await self._resolve_dna_genre_ids(dna)
        results = await self.igdb.query_games(
            genre_ids=genre_ids or None,
            min_rating=80,
            min_rating_count=10,
            released_before=self.CLASSIC_CUTOFF,
            exclude_names=exclude,
            limit=3,
        )
        return self._enrich(results, dna, "ancestry")

    async def recommend_retry(
        self, dna: Dict[str, Any], backlog_names: List[str]
    ) -> List[Dict[str, Any]]:
        """Find a game the user already owns (backlog) that matches their DNA."""
        if not backlog_names:
            return []

        top_tags = set(dna.get("top_tags", []))
        best_match = None
        best_score = -1
        matching_tag = ""

        # Limit to 5 API calls to keep it fast
        for name in backlog_names[:5]:
            game = await self.igdb.get_game_metadata(name)
            if not game:
                continue

            game_tags = set()
            for field in ("genres", "themes", "keywords"):
                items = game.get(field, [])
                if isinstance(items, list):
                    game_tags.update(
                        item["name"] for item in items
                        if isinstance(item, dict) and "name" in item
                    )

            matching = list(top_tags & game_tags)
            score = len(matching)

            if score > best_score:
                best_score = score
                best_match = game
                matching_tag = matching[0] if matching else (list(top_tags)[0] if top_tags else "this genre")

        if not best_match or not isinstance(best_match, dict):
            return []

        best_match["reasoning"] = f"You already own {best_match.get('name')}, and it matches your love for {matching_tag}. You've barely played it — give it another shot!"
        
        # Format the same way as `_enrich`
        return [{
            "name": best_match.get("name", "Unknown"),
            "summary": best_match.get("summary", "No summary available."),
            "cover_url": best_match.get("cover_url", "https://via.placeholder.com/264x352?text=No+Cover"),
            "total_rating": best_match.get("total_rating"),
            "reasoning": best_match["reasoning"],
        }]
