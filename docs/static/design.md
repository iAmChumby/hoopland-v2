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
We use OpenCV and MediaPipe for comprehensive appearance detection.

### Skin Tone Detection
- **Algorithm**: YCrCb color space analysis on skin-masked regions of the headshot
- **Color Space**: YCrCb (better for skin detection than RGB)
- **Mapping**: Average RGB → Hoop Land Skin Code (1-10) via similarity matching

### Facial Landmark Detection
- **Library**: MediaPipe Face Landmarker v0.10+ (Tasks API)
- **Model**: `face_landmarker.task` (468 landmark points)
- **Features**:
  - Ear visibility detection → Hair length estimation
  - Chin polygon extraction → Precise facial hair detection
  - Forehead boundary detection → Hair/forehead separation
- **Fallback**: Basic image analysis if MediaPipe unavailable or detection fails

### Hair & Accessory Detection
- **Method**: Color histogram analysis in specific facial regions
- **Enhanced by**: MediaPipe landmarks for precise region boundaries
- **Output**: Indexed styles matching Hoopland's appearance mapping

## Output Format
The game expects a specific JSON structure. We strictly adhere to the schema reverse-engineered from game save files.
