# Frontend Architecture Plan (Next.js / React)

To support user accounts, manageable settings, and dynamic interactions (like rejecting a recommendation or linking multiple stores), the React interface must become stateful and modular. We will rely heavily on Supabase for auth and Next.js App Router for navigation.

## Application Structure

### 1. Routing Diagram
- `/`: The hero landing page explaining the app.
- `/login`: Supabase Magic Link or OAuth generic login.
- `/dashboard`: The main recommendation interface (the "Sherpa" view).
- `/settings`: Where users manage their connections.
  - `/settings/connections`: Forms for pasting their Steam ID, logging into GOG/Epic.
  - `/settings/preferences`: UI for "Negative Tags" (e.g., "Mute Anime/Visual Novel genres").

### 2. State Management (React Context / Zustand)
We need global state to handle:
- **`userSession`**: Is the user logged in? Which UUID?
- **`connections`**: Does the user have Steam linked? GOG? This determines if we show the "Connect your account" prompt on the dashboard.
- **`dnaProfile`**: The current session's calculated tags and Archetype matches (so we don't re-fetch when they navigate between settings and the dashboard).

### 3. Component Architecture

#### `ConnectionManager.jsx`
- Displays cards for Steam, GOG, Epic, Xbox.
- Tracks sync status (e.g., "Steam: Last synced 2 days ago" -> [Resync] button).
- Handles edge cases like private Steam profiles (shows a helpful tip on how to make them public).

#### `SherpaDashboard.jsx` (The Core UI)
- **Top Section**: The DNA Visualizer. Shows bubbles natively tracking their top genres across all combined libraries.
- **Middle Section**: The Archetype Carousel. Cards for Modern Hit, Hidden Gem, Indie Spirit, Classic, and Retry.
- **Micro-Interactions**:
  - `Hover Cover Image`: Flips to show the IGDB summary.
  - `Reject Button (X)`: "Not my style." This triggers an API call throwing the game into the `negative_tags` or `rejected_games` database column, and immediately pulls a fresh recommendation.
  - `Keep Button (Heart)`: Adds to a simple "Wishlist" stored in Supabase.

### 4. Fetching Strategy
We will use tools like React Query (`@tanstack/react-query`) or SWR.
- **Why?** Since generating recommendations (`/api/analyze`) is an expensive and slightly slow operation, SWR immediately provides caching. If the user navigates away and back, it instantly restores their last generated recommendations instead of showing a loading spinner.

## Design Aesthetic Directives
- Continue pushing the 'Premium' feel requested in the core design doc. 
- Utilize glassmorphism for connection cards to make them feel like native desktop app integrations.
- Implement subtle micro-animations when a new game recommendation is pulled via "Reject".
