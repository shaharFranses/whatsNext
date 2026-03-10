"""
End-to-end test: Steam -> IGDB -> DNA -> Recommendations
Run:  python scripts/test_logic.py
"""

import asyncio
import sys
import os
import json
import logging

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import (
    STEAM_API_KEY,
    STEAM_USER_ID,
    TWITCH_CLIENT_ID,
    TWITCH_CLIENT_SECRET,
    validate,
)
from app.providers.steam import SteamProvider
from app.providers.igdb import IGDBProvider
from app.services.aggregator import TagAggregator
from app.services.recommender import Recommender

# Show IGDB debug info
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")


async def main():
    try:
        validate()
    except RuntimeError as e:
        print(f"\n[!] Configuration Error: {e}")
        return

    steam = SteamProvider(api_key=STEAM_API_KEY)
    igdb = IGDBProvider(client_id=TWITCH_CLIENT_ID, client_secret=TWITCH_CLIENT_SECRET)
    aggregator = TagAggregator(igdb_provider=igdb)
    recommender = Recommender(igdb_provider=igdb)

    # Verify IGDB credentials first
    print("\n[*] Testing IGDB authentication...")
    try:
        token = await igdb._authenticate()
        print(f"[OK] IGDB token acquired: {token[:12]}...")
    except Exception as e:
        print(f"[FAIL] IGDB auth failed: {e}")
        return

    # Fetch ALL Steam games for exclusions and backlog
    print(f"\n[*] Fetching games from Steam for {STEAM_USER_ID}...")
    all_games = await steam.get_owned_games(STEAM_USER_ID)
    all_game_names = [g.get("name") for g in all_games if g.get("name")]
    
    # 30 mins to 3 hours
    backlog_names = [
        g.get("name") for g in all_games
        if g.get("name") and 30 <= g.get("playtime_forever", 0) <= 180
    ]

    print(f"[*] Fetching top 5 games by achievement completion...")
    top_games = await steam.get_top_games_with_achievements(STEAM_USER_ID, n=5)
    dna_game_names = [g.get("name") for g in top_games if g.get("name")]
    print(f"[OK] Top Games (DNA Source): {', '.join(dna_game_names)}")

    # Aggregate tags (DNA)
    print(f"[*] Fetching metadata from IGDB and aggregating tags...")
    dna = await aggregator.get_user_dna(dna_game_names)

    print("\n" + "=" * 55)
    print("  USER GAMING DNA (Top Tags)")
    print("=" * 55)
    for tag in dna["top_tags"]:
        count = dna["tag_distribution"].get(tag, 0)
        print(f"  - {tag:<25} (Found in {count} games)")

    print("\n[*] Game Breakdown:")
    for game, tags in dna["game_breakdown"].items():
        print(f"    > {game}: {', '.join(tags[:5])}")

    # Recommendations
    print("\n" + "=" * 55)
    print("  RECOMMENDATIONS")
    print("=" * 55)

    def print_recs(label, recs):
        print(f"\n  [{label}]")
        if not recs:
            print("    (no results)")
            return
        for game in recs:
            rating = game.get("total_rating")
            rating_str = f"{rating:.1f}" if rating else "N/A"
            print(f"    * {game['name']}  (Rating: {rating_str})")
            print(f"      {game.get('reasoning', '')}")
            print(f"      Cover: {game.get('cover_url', 'N/A')}")

    modern = await recommender.recommend_modern(dna, exclude=all_game_names)
    print_recs("Modern Hit", modern)

    gems = await recommender.recommend_hidden_gem(dna, exclude=all_game_names)
    print_recs("Hidden Gem", gems)

    indie = await recommender.recommend_indie(dna, exclude=all_game_names)
    print_recs("Indie Spirit", indie)

    classics = await recommender.recommend_ancestry(dna, exclude=all_game_names)
    print_recs("Old Masterpiece", classics)

    retry = await recommender.recommend_retry(dna, backlog_names)
    print_recs("Retry (Backlog)", retry)

    print("\n--- Phase 2 Logic Engine Verification Complete ---")


if __name__ == "__main__":
    asyncio.run(main())
