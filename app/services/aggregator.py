from collections import Counter
from typing import Any, Dict, List
from app.providers.igdb import IGDBProvider


class TagAggregator:
    """Aggregates tags from multiple games to find common themes."""

    def __init__(self, igdb_provider: IGDBProvider):
        self.igdb_provider = igdb_provider

    async def get_user_dna(self, game_names: List[str]) -> Dict[str, Any]:
        """
        Build a 'user DNA' map of the most frequent tags across a list of games.
        Returns a dictionary with 'top_tags' and 'all_tags_count'.
        """
        tags_map = await self.igdb_provider.get_tags_for_games(game_names)
        
        all_tags = []
        for tags in tags_map.values():
            all_tags.extend(tags)

        tag_counts = Counter(all_tags)
        
        # Sort tags by frequency (most common first)
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        top_tags = [str(tag) for tag, count in sorted_tags[:10]]
        
        return {
            "top_tags": top_tags,
            "tag_distribution": dict(sorted_tags),
            "game_breakdown": tags_map
        }
