-- Create custom Enum for store providers
CREATE TYPE provider_type AS ENUM ('steam', 'gog', 'epic', 'xbox');

-- 1. `user_profiles` table
CREATE TABLE public.user_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS on user_profiles
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can see their own profile
CREATE POLICY "Users can view own profile" 
ON public.user_profiles FOR SELECT 
USING (auth.uid() = user_id);

-- Policy: Users can insert their own profile
CREATE POLICY "Users can insert own profile" 
ON public.user_profiles FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile" 
ON public.user_profiles FOR UPDATE 
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);


-- 2. `provider_connections` table
CREATE TABLE public.provider_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider_name provider_type NOT NULL,
    provider_account_id TEXT NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, provider_name)
);

-- Enable RLS on provider_connections
ALTER TABLE public.provider_connections ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own connections
CREATE POLICY "Users can view own connections" 
ON public.provider_connections FOR SELECT 
USING (auth.uid() = user_id);
-- (Writes happen via backend service role bypassing RLS)


-- 3. `user_gaming_dna` table
CREATE TABLE public.user_gaming_dna (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    top_genres JSONB DEFAULT '[]'::jsonb,
    top_themes JSONB DEFAULT '[]'::jsonb,
    negative_tags JSONB DEFAULT '[]'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS on user_gaming_dna
ALTER TABLE public.user_gaming_dna ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own DNA
CREATE POLICY "Users can view own DNA" 
ON public.user_gaming_dna FOR SELECT 
USING (auth.uid() = user_id);


-- 4. `cached_library` table
CREATE TABLE public.cached_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider_name provider_type NOT NULL,
    game_name TEXT NOT NULL,
    playtime_minutes INTEGER DEFAULT 0,
    completion_percentage FLOAT,
    last_played_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, provider_name, game_name)
);

-- Enable RLS on cached_library
ALTER TABLE public.cached_library ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own library
CREATE POLICY "Users can view own library" 
ON public.cached_library FOR SELECT 
USING (auth.uid() = user_id);


-- Create trigger to automatically create a profile for new users
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
DECLARE
    v_username TEXT;
BEGIN
    -- Try to get username from metadata
    v_username := new.raw_user_meta_data->>'username';
    
    -- Fallback: Use email prefix if username is missing
    IF v_username IS NULL THEN
        v_username := split_part(new.email, '@', 1) || '_' || substr(md5(random()::text), 1, 6);
    END IF;

    INSERT INTO public.user_profiles (user_id, username)
    VALUES (new.id, v_username);
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
