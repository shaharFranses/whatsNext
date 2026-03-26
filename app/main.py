from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from typing import Dict, Any, Optional
import os
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

from app.config import (
    STEAM_API_KEY,
    TWITCH_CLIENT_ID,
    TWITCH_CLIENT_SECRET,
    ALLOWED_ORIGINS,
    validate
)
from app.auth import get_current_user
from app.providers.steam import SteamProvider
from app.providers.igdb import IGDBProvider
from app.services.aggregator import TagAggregator
from app.services.recommender import Recommender

validate()

# Initialize providers and services
steam_provider = SteamProvider(api_key=STEAM_API_KEY)
igdb_provider = IGDBProvider(
    client_id=TWITCH_CLIENT_ID,
    client_secret=TWITCH_CLIENT_SECRET,
)
aggregator = TagAggregator(igdb_provider=igdb_provider)
recommender = Recommender(igdb_provider=igdb_provider)

# Request Models
class SignupRequest(BaseModel):
    email: str
    password: str
    username: str

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None

class SyncRequest(BaseModel):
    steam_id: str

    @field_validator("steam_id")
    @classmethod
    def validate_steam_id(cls, v: str) -> str:
        if not re.fullmatch(r"\d{17}", v.strip()):
            raise ValueError("steam_id must be a 17-digit number")
        return v.strip()

app = FastAPI(title="What Next", version="0.1.0")

# Serve frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def read_index():
    return FileResponse(frontend_path / "index.html")

# Enable CORS — restrict to configured origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/me")
async def get_me(user: Any = Depends(get_current_user)):
    """Return the currently authenticated user's metadata."""
    return {
        "id": user.id,
        "email": user.email,
        "last_sign_in_at": user.last_sign_in_at
    }


@app.post("/api/auth/signup")
async def signup(data: SignupRequest):
    """
    Wrapper for Supabase signup. 
    Passes username as user_metadata so the DB trigger can pick it up.
    """
    try:
        from app.db import supabase
        res = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
            "options": {
                "data": {
                    "username": data.username
                }
            }
        })
        return {"status": "success", "user": res.user}
    except Exception as e:
        logger.error("Signup error: %s", e)
        raise HTTPException(status_code=400, detail="Signup failed. Please check your details and try again.")


@app.put("/api/profiles/me")
async def update_profile(data: ProfileUpdate, user: Any = Depends(get_current_user)):
    """Update the current user's profile in the database."""
    from app.services.db_service import DBService
    success = DBService.upsert_user_profile(
        user_id=user.id,
        username=data.username,
        avatar_url=data.avatar_url
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update profile")
    return {"status": "success"}


@app.get("/api/dna/me")
async def get_my_dna(user: Any = Depends(get_current_user)):
    """Fetch the current user's saved gaming DNA."""
    from app.services.db_service import DBService
    dna = DBService.get_gaming_dna(user.id)
    if not dna:
        return {"status": "empty", "genres": [], "themes": []}
    return {
        "status": "success",
        "genres": dna.get("top_genres", []),
        "themes": dna.get("top_themes", []),
        "updated_at": dna.get("updated_at")
    }


@app.post("/api/steam/sync")
async def sync_steam_library(data: SyncRequest, user: Any = Depends(get_current_user)):
    """Fetch Steam library and cache it in the database."""
    from app.services.db_service import DBService
    try:
        # 1. Fetch from Steam
        games = await steam_provider.get_owned_games(data.steam_id)
        if not games:
             raise HTTPException(status_code=404, detail="No games found for this Steam ID.")

        # 2. Update connection link
        DBService.upsert_provider_connection(
            user_id=user.id,
            provider_name="steam",
            account_id=data.steam_id
        )

        # 3. Sync library cache
        # DBService expects a specific format
        formatted_games = []
        for g in games:
            formatted_games.append({
                "game_name": g.get("name"),
                "playtime_minutes": g.get("playtime_forever", 0),
                "last_played_at": None # Steam V1 doesn't always provide this in the main list easily
            })
        
        DBService.sync_cached_library(user.id, "steam", formatted_games)
        
        return {"status": "success", "game_count": len(games)}
    except Exception as e:
        logger.error("Steam sync error for user %s: %s", user.id, e)
        raise HTTPException(status_code=500, detail="Failed to sync Steam library. Please try again.")


@app.get("/api/analyze/{steam_id}")
async def analyze_steam_profile(
    steam_id: Optional[str] = None, 
    user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Orchestrate the recommendation pipeline.
    If steam_id is omitted, we use the linked Steam ID from the database.
    """
    from app.services.db_service import DBService
    
    if steam_id and not re.fullmatch(r"\d{17}", steam_id):
        raise HTTPException(status_code=400, detail="Invalid Steam ID format. Must be a 17-digit number.")

    target_steam_id = steam_id

    # 1. Resolve Steam ID if not provided
    if not target_steam_id:
        connections = DBService.get_provider_connections(user.id)
        steam_conn = next((c for c in connections if c["provider_name"] == "steam"), None)
        if not steam_conn:
            raise HTTPException(status_code=400, detail="No Steam account linked. Please provide a Steam ID or link your account.")
        target_steam_id = steam_conn["provider_account_id"]

    try:
        # 2. Fetch or Use Cached Library
        # For simplicity in this first ver, we'll fetch fresh but we'll use the resolved ID
        all_games = await steam_provider.get_owned_games(target_steam_id)
        all_game_names = [g.get("name") for g in all_games if g.get("name")]
        
        # Build backlog (games played between 30 mins and 3 hours)
        backlog_names = [
            g.get("name") for g in all_games
            if g.get("name") and 30 <= g.get("playtime_forever", 0) <= 180
        ]

        # 1. Fetch top 5 games with achievement data (the new hybrid DNA source)
        top_games = await steam_provider.get_top_games_with_achievements(target_steam_id, n=5)
        if not top_games:
            raise HTTPException(status_code=404, detail="No Steam games found for this ID.")
        
        dna_game_names = [g.get("name") for g in top_games if g.get("name")]
        
        # 2. Get User DNA (tags)
        # Refactored TagAggregator now provides separate buckets
        dna_data = await aggregator.get_user_dna(dna_game_names)
        
        # PERSIST: Save DNA to DB for future use in the dashboard
        DBService.upsert_gaming_dna(
            user_id=user.id,
            top_genres=dna_data.get("top_genres", []),
            top_themes=dna_data.get("top_themes", [])
        )
        
        # 3. Generate Recommendations (exclude ALL owned games)
        modern_hits = await recommender.recommend_modern(dna_data, exclude=all_game_names)
        hidden_gems = await recommender.recommend_hidden_gem(dna_data, exclude=all_game_names)
        indie_picks = await recommender.recommend_indie(dna_data, exclude=all_game_names)
        classics = await recommender.recommend_ancestry(dna_data, exclude=all_game_names)
        retry_picks = await recommender.recommend_retry(dna_data, backlog_names)
        
        # 4. Format for Frontend
        return {
            "dna": dna_data.get("top_genres", []) + dna_data.get("top_themes", []), # Combined for display
            "dna_detailed": {
                "genres": dna_data.get("top_genres"),
                "themes": dna_data.get("top_themes")
            },
            "recommendations": {
                "modern": modern_hits[0] if modern_hits else {"name": "N/A", "reasoning": "No modern match found."},
                "gem": hidden_gems[0] if hidden_gems else {"name": "N/A", "reasoning": "No hidden gem found."},
                "indie": indie_picks[0] if indie_picks else {"name": "N/A", "reasoning": "No indie pick found."},
                "classic": classics[0] if classics else {"name": "N/A", "reasoning": "No classic found."},
                "retry": retry_picks[0] if retry_picks else {"name": "N/A", "reasoning": "No backlog games match your DNA right now."},
            }
        }

    except Exception as e:
        logger.error("Analysis error for steam_id %s: %s", target_steam_id, e)
        raise HTTPException(status_code=500, detail="Failed to generate recommendations. Please try again.")
