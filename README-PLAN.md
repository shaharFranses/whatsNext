1. Executive Summary

Goal: A persistent, web-based "Gaming Sherpa" that saves user progress, analyzes Steam/GOG DNA, and provides interactive paths.

Core Philosophy: Identity first. Analysis second. Interactive discovery third.

2. Technical Stack

Backend: Python (FastAPI).

Database/Auth: Supabase (PostgreSQL + Auth) – Crucial for saving the user's Email and SteamID link.

Frontend: Next.js + Tailwind CSS + Framer Motion (for those smooth "analyzing" animations).

APIs: Steam OpenID, IGDB (Twitch), OpenAI/Gemini (for the Concierge).

3. Phase 0: Identity & Persistence (The New Foundation)

Task 0.1: Setup Supabase project and link to FastAPI.

Task 0.2: Implement Email Login (Magic Link or Social).

Task 0.3: Implement Steam OpenID Link. User logs in once; we store their steam_id in the profiles table.

Verification: User can log in, link Steam, and see their email and SteamID on a "Profile" page. Stop and wait for user approval.

4. Phase 1: The "DNA" Pipeline

Task 1.1: Fetch GetOwnedGames for the linked steam_id.

Task 1.2: Playstyle DNA Algorithm: Instead of just sorting by playtime, categorize the user into a Persona (e.g., "The Tactician," "The Completionist") based on achievement percentages.

Verification: Display the user's "Gaming Persona" and their Top 5 games with DNA tags. Stop and wait for user approval.

5. Phase 2: The Logic Engine (The Sherpa)

Task 2.1: IGDB Integration (OAuth2 token management).

Task 2.2: The Four Paths Logic: * Modern Choice: High popularity + matching DNA.

Hidden Gem: Rating > 80% + Total Reviews < 1000.

Indie Spirit: Indie tag + High "stickiness" (avg. playtime).

Old Masterpiece: Ancestry mapping (e.g., if DNA = "Extraction Shooter," suggest Marathon).

Verification: API returns 4 distinct game objects with "Why we picked this" strings. Stop and wait for user approval.

6. Phase 3: The Interactive Dashboard

Task 3.1: Build the "Analyzing" state (Live ticker with persona-based messages).

Task 3.2: Build Interactive Path Cards. Include a "Not for me" button that triggers a re-roll.

Task 3.3: LLM Concierge Component: A chat window that knows the user's hardware (optional) and the game's setup requirements.