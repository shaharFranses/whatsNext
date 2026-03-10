"""
Quick test script -- prints your top 5 Steam games with achievement completion.
Run:  python scripts/test_steam.py
"""

import asyncio
import json
import sys
import os

# Ensure project root is on the path so we can import app.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import STEAM_API_KEY, STEAM_USER_ID, validate
from app.providers.steam import SteamProvider


async def main():
    validate()

    provider = SteamProvider(api_key=STEAM_API_KEY)
    print(f"\n[*] Fetching top 5 games + achievements for Steam ID: {STEAM_USER_ID} ...")
    print("    (this may take a few seconds)\n")

    results = await provider.get_top_games_with_achievements(steam_id=STEAM_USER_ID, n=5)

    # Pretty table
    print(f"{'#':<4} {'Game':<45} {'Hours':>7} {'Achievements':>15}")
    print("-" * 75)
    for i, game in enumerate(results, start=1):
        ach = game["achievements"]
        if ach:
            ach_str = f"{ach['achieved']}/{ach['total']} ({ach['completion_pct']}%)"
        else:
            ach_str = "N/A"
        print(f"{i:<4} {game['name']:<45} {game['playtime_hours']:>6.1f}h {ach_str:>15}")

    # Full JSON output for verification
    print("\n--- Full JSON ---")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print()


if __name__ == "__main__":
    asyncio.run(main())
