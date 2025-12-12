# Hoopland V2 Generator

A tool to generate custom league and draft class files for the mobile game **Hoop Land** using real-world NBA and NCAA data.

## Features
- **NBA & NCAA Support**: Generate full leagues for any season from ~2000 to present.
- **Draft Classes**: Generate incoming rookie classes with accurate attributes.
- **Auto-Appearance**: Uses Computer Vision (OpenCV) to automatically determine player skin tone and hair color from headshots.
- **Rating Normalization**: Converts real stats into balanced game ratings (1-10 scale).

## Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Requires `opencv-python-headless`.*

## Usage
Run the CLI from the project root:

```bash
# Generate an NBA League
python src/hoopland/cli.py --league nba --year 2003

# Generate a Draft Class
python src/hoopland/cli.py --league draft --year 2003
```

## Development
- **Testing**: Run `pytest` to run the test suite.
- **Linting**: Run `ruff check .` to verify code quality.
- **Documentation**: See `docs/static/` for detailed Architecture and Design docs.

## Output
Generated files are saved to `output/{YEAR}/`.
