import sys
import os

# Ensure project root is in path
sys.path.append(r"c:\Program Files (x86)\projects\whats next")

from app.db import supabase

def create_user():
    print("=== Creating Test User via Admin API ===")
    
    email = "testemail@com"
    password = "123456789"
    username = "testname"
    
    try:
        # 1. Create user with metadata
        # Setting email_confirm=True so we can login immediately
        print(f"[1] Attempting to create user: {email} with username: {username}...")
        print("    Calling supabase.auth.admin.create_user...")
        res = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "user_metadata": {"username": username},
            "email_confirm": True
        })
        print("    API Call successful.")
        
        user_id = res.user.id
        print(f"  [OK] User created successfully. ID: {user_id}")
        
        # 2. Verify profile creation (trigger should have handled this)
        print("\n[2] Verifying public.user_profiles entry...")
        profile_res = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
        
        if profile_res.data:
            print(f"  [OK] Profile found: {profile_res.data[0]}")
        else:
            print("  [FAIL] Profile was not created by trigger.")
            
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")

if __name__ == "__main__":
    create_user()
