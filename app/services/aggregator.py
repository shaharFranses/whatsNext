from collections import Counter
from typing import Any, Dict, List
from app.providers.igdb import IGDBProvider


class TagAggregator:
    """Aggregates tags from multiple games to find common themes."""

    def __init__(self, igdb_provider: IGDBProvider):
        self.igdb_provider = igdb_provider

    async def get_user_dna(self, game_names: List[str]) -> Dict[str, Any]:
        """
        Build a 'user DNA' map by aggregating genres, themes, and keywords separately.
        """
        tags_map = await self.igdb_provider.get_tags_for_games(game_names)
        
        counts = {
            "genres": Counter(),
            "themes": Counter(),
            "keywords": Counter()
        }

        for game_data in tags_map.values():
            for field in counts.keys():
                counts[field].update(game_data.get(field, []))

        # Helper to get sorted list from Counter
        def get_top(counter, n=10):
            return [str(item) for item, count in counter.most_common(n)]

        top_genres = get_top(counts["genres"])
        top_themes = get_top(counts["themes"])
        top_keywords = get_top(counts["keywords"])
        
        # We still provide a legacy 'top_tags' for backward compatibility with current Recommender
        # But we'll update Recommender next to use the better structure.
        top_tags = list(set(top_genres + top_themes + top_keywords))[:10]

        return {
            "top_genres": top_genres,
            "top_themes": top_themes,
            "top_keywords": top_keywords,
            "top_tags": top_tags, # Compatibility
            "all_counts": {k: dict(v) for k, v in counts.items()},
            "game_breakdown": tags_map
        }
