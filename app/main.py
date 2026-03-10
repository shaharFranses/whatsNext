from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, Any
import os
from pathlib import Path

from app.config import (
    STEAM_API_KEY, 
    TWITCH_CLIENT_ID, 
    TWITCH_CLIENT_SECRET, 
    validate
)
from app.providers.steam import SteamProvider
from app.providers.igdb import IGDBProvider
from app.services.aggregator import TagAggregator
from app.services.recommender import Recommender

# Initialize providers and services
steam_provider = SteamProvider(api_key=STEAM_API_KEY)
igdb_provider = IGDBProvider(
    client_id=TWITCH_CLIENT_ID,
    client_secret=TWITCH_CLIENT_SECRET,
)
aggregator = TagAggregator(igdb_provider=igdb_provider)
recommender = Recommender(igdb_provider=igdb_provider)

app = FastAPI(title="What Next", version="0.1.0")

# Serve frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def read_index():
    return FileResponse(frontend_path / "index.html")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/analyze/{steam_id}")
async def analyze_steam_profile(steam_id: str) -> Dict[str, Any]:
    """
    Orchestrate the recommendation pipeline:
    1. Fetch top games from Steam.
    2. Aggregate tags/DNA.
    3. Generate recommendations for archetypes.
    4. Format for frontend.
    """
    try:
        # 0. Fetch ALL owned games to build exclusions and backlog
        all_games = await steam_provider.get_owned_games(steam_id)
        all_game_names = [g.get("name") for g in all_games if g.get("name")]
        
        # Build backlog (games played between 30 mins and 3 hours)
        backlog_names = [
            g.get("name") for g in all_games
            if g.get("name") and 30 <= g.get("playtime_forever", 0) <= 180
        ]

        # 1. Fetch top 5 games with achievement data (the new hybrid DNA source)
        top_games = await steam_provider.get_top_games_with_achievements(steam_id, n=5)
        if not top_games:
            raise HTTPException(status_code=404, detail="No Steam games found for this ID.")
        
        dna_game_names = [g.get("name") for g in top_games if g.get("name")]
        
        # 2. Get User DNA (tags)
        dna_data = await aggregator.get_user_dna(dna_game_names)
        dna_tags = dna_data.get("top_tags", [])
        
        # 3. Generate Recommendations (exclude ALL owned games)
        modern_hits = await recommender.recommend_modern(dna_data, exclude=all_game_names)
        hidden_gems = await recommender.recommend_hidden_gem(dna_data, exclude=all_game_names)
        indie_picks = await recommender.recommend_indie(dna_data, exclude=all_game_names)
        classics = await recommender.recommend_ancestry(dna_data, exclude=all_game_names)
        retry_picks = await recommender.recommend_retry(dna_data, backlog_names)
        
        # 4. Format for Frontend
        return {
            "dna": dna_tags,
            "recommendations": {
                "modern": modern_hits[0] if modern_hits else {"name": "N/A", "reasoning": "No modern match found."},
                "gem": hidden_gems[0] if hidden_gems else {"name": "N/A", "reasoning": "No hidden gem found."},
                "indie": indie_picks[0] if indie_picks else {"name": "N/A", "reasoning": "No indie pick found."},
                "classic": classics[0] if classics else {"name": "N/A", "reasoning": "No classic found."},
                "retry": retry_picks[0] if retry_picks else {"name": "N/A", "reasoning": "No backlog games match your DNA right now."},
            }
        }

    except Exception as e:
        print(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
