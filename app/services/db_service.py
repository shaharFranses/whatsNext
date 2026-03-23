import logging
from typing import Dict, Any, List, Optional
from app.db import supabase

logger = logging.getLogger(__name__)

class DBService:
    @staticmethod
    def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error fetching profile for {user_id}: {e}")
            return None

    @staticmethod
    def upsert_user_profile(user_id: str, username: str = None, avatar_url: str = None) -> bool:
        try:
            data = {"user_id": user_id}
            if username:
                data["username"] = username
            if avatar_url:
                data["avatar_url"] = avatar_url
                
            supabase.table("user_profiles").upsert(data, on_conflict="user_id").execute()
            return True
        except Exception as e:
            logger.error(f"Error upserting profile for {user_id}: {e}")
            return False

    @staticmethod
    def get_provider_connections(user_id: str) -> List[Dict[str, Any]]:
        try:
            res = supabase.table("provider_connections").select("*").eq("user_id", user_id).execute()
            return res.data
        except Exception as e:
            logger.error(f"Error fetching connections for {user_id}: {e}")
            return []

    @staticmethod
    def upsert_provider_connection(user_id: str, provider_name: str, account_id: str, token: str = None) -> bool:
        try:
            data = {
                "user_id": user_id,
                "provider_name": provider_name,
                "provider_account_id": account_id
            }
            if token:
                data["access_token"] = token
                
            supabase.table("provider_connections").upsert(
                data, 
                on_conflict="user_id, provider_name"
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error upserting connection for {user_id} ({provider_name}): {e}")
            return False

    @staticmethod
    def delete_provider_connection(user_id: str, provider_name: str) -> bool:
        try:
            supabase.table("provider_connections").delete().eq("user_id", user_id).eq("provider_name", provider_name).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting connection for {user_id} ({provider_name}): {e}")
            return False

    @staticmethod
    def get_gaming_dna(user_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = supabase.table("user_gaming_dna").select("*").eq("user_id", user_id).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error fetching DNA for {user_id}: {e}")
            return None

    @staticmethod
    def upsert_gaming_dna(user_id: str, top_genres: list, top_themes: list, negative_tags: list = None) -> bool:
        try:
            data = {
                "user_id": user_id,
                "top_genres": top_genres,
                "top_themes": top_themes,
            }
            if negative_tags is not None:
                data["negative_tags"] = negative_tags
                
            supabase.table("user_gaming_dna").upsert(data, on_conflict="user_id").execute()
            return True
        except Exception as e:
            logger.error(f"Error upserting DNA for {user_id}: {e}")
            return False

    @staticmethod
    def get_cached_library(user_id: str, provider_name: str = None) -> List[Dict[str, Any]]:
        try:
            query = supabase.table("cached_library").select("*").eq("user_id", user_id)
            if provider_name:
                query = query.eq("provider_name", provider_name)
            res = query.execute()
            return res.data
        except Exception as e:
            logger.error(f"Error fetching library for {user_id}: {e}")
            return []

    @staticmethod
    def sync_cached_library(user_id: str, provider_name: str, games: List[Dict[str, Any]]) -> bool:
        """
        games should be a list of dicts with:
        ['game_name', 'playtime_minutes', 'completion_percentage', 'last_played_at']
        """
        try:
            # 1. Delete old cache for this provider
            supabase.table("cached_library").delete().eq("user_id", user_id).eq("provider_name", provider_name).execute()
            
            # 2. Insert new cache in chunks of 500 mapping to the right columns
            chunk_size = 500
            for i in range(0, len(games), chunk_size):
                chunk = games[i:i + chunk_size]
                formatted_chunk = []
                for g in chunk:
                    formatted_chunk.append({
                        "user_id": user_id,
                        "provider_name": provider_name,
                        "game_name": g.get("game_name"),
                        "playtime_minutes": g.get("playtime_minutes", 0),
                        "completion_percentage": g.get("completion_percentage"),
                        "last_played_at": g.get("last_played_at")
                    })
                if formatted_chunk:
                    supabase.table("cached_library").insert(formatted_chunk).execute()
            return True
        except Exception as e:
            logger.error(f"Error syncing library for {user_id} ({provider_name}): {e}")
            return False
