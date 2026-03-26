import os
from dotenv import load_dotenv

load_dotenv()

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_USER_ID = os.getenv("STEAM_USER_ID")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Comma-separated list of allowed frontend origins. Defaults to localhost dev.
_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
ALLOWED_ORIGINS = [o.strip() for o in _origins_raw.split(",") if o.strip()]

def validate():
    """Raise early if required env vars are missing."""
    missing = []
    if not STEAM_API_KEY:
        missing.append("STEAM_API_KEY")
    if not STEAM_USER_ID:
        missing.append("STEAM_USER_ID")
    if not TWITCH_CLIENT_ID:
        missing.append("TWITCH_CLIENT_ID")
    if not TWITCH_CLIENT_SECRET:
        missing.append("TWITCH_CLIENT_SECRET")
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_SERVICE_KEY:
        missing.append("SUPABASE_SERVICE_KEY")

    if missing:
        steam_missing = [m for m in missing if "STEAM" in m]
        supabase_missing = [m for m in missing if "SUPABASE" in m]
        igdb_missing = [m for m in missing if m in ("TWITCH_CLIENT_ID", "TWITCH_CLIENT_SECRET")]

        if steam_missing:
            raise RuntimeError(
                f"Missing required Steam environment variables: {', '.join(steam_missing)}. "
                "Copy .env.template to .env and fill in your values."
            )
        if supabase_missing:
            raise RuntimeError(
                f"Missing required Supabase environment variables: {', '.join(supabase_missing)}. "
                "Copy .env.template to .env and fill in your values."
            )
        if igdb_missing:
            import logging
            logging.getLogger(__name__).warning(
                "Missing IGDB credentials (%s). IGDBProvider will run in MOCK MODE.",
                ", ".join(igdb_missing)
            )
