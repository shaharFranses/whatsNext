# Database Architecture Plan (Supabase PostgreSQL)

To support user accounts, multiple store integrations (Steam, GOG, Epic), and persistent analysis, we will use Supabase PostgreSQL. This allows us to sync libraries in the background and generate instant recommendations without constantly hitting rate limits.

## Core Tables

### 1. `users` (Managed by Supabase Auth)
Native Supabase authentication table. We will rely on this for secure session management and row-level security (RLS).
- `id`: UUID (Primary Key)
- `email`: String
- `created_at`: Timestamp

### 2. `user_profiles`
Public-facing user details and global app preferences.
- `user_id`: UUID (Foreign Key to auth.users, Primary Key)
- `username`: String (Unique)
- `avatar_url`: String (Optional)
- `created_at`: Timestamp

### 3. `provider_connections`
Stores the external IDs and necessary authentication tokens for third-party stores. 
- `id`: UUID (Primary Key) # Some users might have multiple accounts? Usually just 1 per provider.
- `user_id`: UUID (Foreign Key to auth.users)
- `provider_name`: Enum (`steam`, `gog`, `epic`, `xbox`)
- `provider_account_id`: String (e.g., the 17-digit SteamID64)
- `access_token`: String (If OAuth is required, e.g., Epic/Xbox)
- `refresh_token`: String
- `last_sync_at`: Timestamp (When we last pulled their library)
- **Constraint**: Unique (`user_id`, `provider_name`)

### 4. `user_gaming_dna`
Caches the calculated "Gaming DNA" so the frontend can load it instantly on the dashboard without waiting for the Aggregator to re-run.
- `user_id`: UUID (Foreign Key to auth.users, Primary Key)
- `top_genres`: JSONB (e.g., `["Strategy", "RPG"]`)
- `top_themes`: JSONB
- `negative_tags`: JSONB (Tags the user explicitly disliked/wants excluded)
- `updated_at`: Timestamp

### 5. `cached_library` (Optional but Recommended)
Instead of asking Steam/GOG for the user's games every time they click "Analyze", we sync their games into our own database. 
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key to auth.users)
- `provider_name`: Enum
- `game_name`: String
- `playtime_minutes`: Integer
- `completion_percentage`: Float (Achievement tracking)
- `last_played_at`: Timestamp
- **Constraint**: Unique (`user_id`, `provider_name`, `game_name`)

## Security (Row Level Security)
All tables use RLS so that users can only access their own data (`user_id == auth.uid()`):
- **`user_profiles`**: `SELECT`, `INSERT`, `UPDATE` own row. `DELETE` is optional (account deletion flow).
- **`provider_connections`**: `SELECT` own rows only. All writes (`INSERT`/`UPDATE`/`DELETE`) go through the backend API to validate OAuth tokens and cascade cleanup.
- **`user_gaming_dna`**: `SELECT`, `UPDATE` own row (only the backend service should `INSERT`).
- **`cached_library`**: `SELECT` own rows (only the backend sync service should `INSERT`/`UPDATE`/`DELETE`).
