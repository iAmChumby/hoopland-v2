# Architecture Overview

## Core System
The Hoopland V2 Generator transforms real-world basketball data (NBA/NCAA) into Hoop Land save files (`.txt`/`.json`).

## Components
### 1. CLI Entry Point (`src/hoopland/cli.py`)
Handles user arguments (`--year`, `--league`) and orchestrates the generation process.

### 2. Generator (`src/hoopland/blocks/generator.py`)
main logic block that ties together data fetching, processing, and output formatting.

### 3. Data Layer
- **NBA Client**: Fetches stats from `nba_api`.
- **Repository**: (Planned) Caching layer using SQLite to determine whether to fetch fresh data or use local cache.

### 4. Engines
- **Stats Engine**: Normalizes real stats (0-100) to Hoop Land ratings (1-10).
- **CV Engine**: Analyzes player headshots to determine skin tone and hair color.

## Data Flow
1. User requests a Season (e.g., 2003 NBA).
2. Generator requests Roster + Stats.
3. Generator requests Draft Class (if applicable).
4. CV Engine processes images for appearance data.
5. Generator assembles the League object.
6. JSON Serializer writes the output file.
