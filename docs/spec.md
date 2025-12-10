Hoop Land CLI - Reimplementation Specification

1. Architecture Overview

The system moves from a "Scrape & Process" model to a "Cache & Query" model.

Old Flow:
Request -> Scrape HTML -> Parse -> Save CSV -> Process (Fragile, slow)

New Flow:
Request -> Check DB -> (If Empty) Fetch API -> Store DB -> Query DB -> Generate JSON (Robust, instant)

Core Components

Repository Layer: The single source of truth. It decides whether to fetch from the web or read from SQLite.

API Clients: Wrappers for nba_api (NBA) and ESPN (NCAA).

CV Engine: Analyzes player headshots to determine skin tone codes (0-10) for Hoop Land.

Stats Engine: Normalizes real stats (0-100 scales) into Hoop Land ratings (1-10 scales).

2. Data Sources

NBA Data (2000-2025)

Source: nba_api (Python library wrapping stats.nba.com).

Endpoints:

CommonTeamRoster: Height, Weight, Age, Player IDs.

LeagueDashPlayerStats: Per-game stats for the entire league in one request.

DraftHistory: Historical draft data.

NCAA Data (2002-2025)

Source: ESPN hidden public API (JSON).

Base URL: http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball

Strategy: Fetch team rosters which include player stats in the JSON payload. This avoids scraping HTML tables.

3. Database Schema (SQLite)

We use SQLAlchemy for ORM mapping. The database hoopland.db will be created automatically.

Table: players

id (PK): internal ID

source_id: NBA/ESPN ID

league: 'NBA' or 'NCAA'

season: '2023-24'

name: String

team_id: String

raw_stats: JSON (The full API payload)

appearance: JSON (Cached CV results: skin_tone, hair_color)

4. Computer Vision (CV) Logic

Goal: Automatically determine skin tone for the game file.

Fetch: Construct headshot URL.

NBA: https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{player_id}.png

ESPN: URL provided in roster JSON.

Process:

Load image into OpenCV (cv2).

Detect face (optional, or center crop).

Convert to YCrCb color space (better for skin detection than RGB).

Mask non-skin pixels.

Calculate average color of the skin mask.

Map: Convert average RGB -> Hoop Land Skin Code (1-10) using K-Nearest Neighbors on a pre-defined palette.

5. Stat Normalization Logic

Hoop Land uses a 1-10 scale (which displays as 1-5 stars).

Formula:
Rating = (PlayerStat - MinStat) / (MaxStat - MinStat) * 10

Shooting: Weighted mix of FG% (Efficiency) and FGA (Volume).

Dribbling: AST + TOV ratio (inverse).

Defense: STL + BLK + DefRating (if available).

6. Implementation Steps

Phase 1: Foundation (Current Step)

Set up requirements.txt and .env.

Initialize SQLite DB.

Create DataRepository to abstract data access.

Phase 2: CV & Appearance

Implement src/hoopland/cv/appearance.py.

Run a script to "backfill" appearances for cached players.

Phase 3: Integration

Update workflows.py to use DataRepository.

Feed the fetched/cached data into StatsConverter.