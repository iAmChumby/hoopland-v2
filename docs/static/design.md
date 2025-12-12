# Design Decisions

## Data Sources
- **NBA**: utilizing `nba_api` because it is robust and wraps the official stats.nba.com endpoints.
- **NCAA**: utilizing ESPN's hidden API because there is no official public NCAA data source that is easily accessible without scraping HTML.

## Rating Normalization
Hoop Land uses a 1-10 scale (displayed as stars).
Real stats are normalized using Min-Max scaling against historical bounds.
- Example: 3PT Rating = (Player3P% - 0.25) / (0.45 - 0.25) * 10
- We clamp values to ensure they stay within valid game ranges.

## Appearance Logic
We use OpenCV to detect skin tone to avoid manual entry.
- **Algorithm**: YCrCb color space analysis on the center crop of the headshot.
- **Fallback**: Default to medium skin tone if image fetch fails.

## Output Format
The game expects a specific JSON structure. We strictly adhere to the schema reverse-engineered from game save files.
