import os
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_KEY

def get_supabase() -> Client:
    """
    Initialize and return a Supabase client using the service role key.
    This client bypasses RLS and should only be used in protected backend routes.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Singleton client instance
supabase = get_supabase()
