"""
Download NCAA team logos from league file and resize them to 256x256.

Usage:
    python scripts/download_and_resize_logos.py <league_file>

Example:
    python scripts/download_and_resize_logos.py output/2016/NCAA_2016_Tournament_League.txt
"""

import json
import sys
import re
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO


def slugify(text: str) -> str:
    """Convert team name to a filename-safe slug."""
    # Lowercase and replace special characters
    text = text.lower()
    text = re.sub(r"[''`]", "", text)  # Remove apostrophes
    text = re.sub(r"[&]", "and", text)  # Replace & with 'and'
    text = re.sub(r"[^a-z0-9\s-]", "", text)  # Remove other special chars
    text = re.sub(r"[\s_]+", "-", text)  # Replace spaces/underscores with dashes
    text = re.sub(r"-+", "-", text)  # Remove multiple dashes
    text = text.strip("-")  # Remove leading/trailing dashes
    return text


def download_image(url: str) -> Image.Image | None:
    """Download an image from URL and return as PIL Image."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content))
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return None


def resize_image(img: Image.Image, size: tuple[int, int] = (256, 256)) -> Image.Image:
    """Resize image to the specified size, maintaining RGBA for transparency."""
    # Convert to RGBA if not already (preserve transparency)
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Use high-quality resampling
    return img.resize(size, Image.Resampling.LANCZOS)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/download_and_resize_logos.py <league_file>")
        print(
            "Example: python scripts/download_and_resize_logos.py output/2016/NCAA_2016_Tournament_League.txt"
        )
        sys.exit(1)

    league_file = Path(sys.argv[1])
    if not league_file.exists():
        print(f"Error: League file not found: {league_file}")
        sys.exit(1)

    # Output directory for NCAA logos
    output_dir = Path("assets/logos/teams/ncaa")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load league data
    print(f"Loading league data from: {league_file}")
    with open(league_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    teams = data.get("teams", [])
    print(f"Found {len(teams)} teams")
    print(f"Downloading and resizing logos to: {output_dir}")
    print("-" * 60)

    success_count = 0
    failed_count = 0

    for team in teams:
        city = team.get("city", "")
        name = team.get("name", "")
        logo_url = team.get("logoURL", "")

        full_name = f"{city} {name}".strip()
        slug = slugify(full_name)

        if not logo_url:
            print(f"[!] {full_name}: No logo URL")
            failed_count += 1
            continue

        output_path = output_dir / f"{slug}.png"

        # Skip if already exists
        if output_path.exists():
            print(f"[OK] {full_name}: Already exists ({slug}.png)")
            success_count += 1
            continue

        print(f"[DL] {full_name}: Downloading...", end=" ")

        img = download_image(logo_url)
        if img is None:
            print("FAILED")
            failed_count += 1
            continue

        # Resize to 256x256
        img = resize_image(img, (256, 256))

        # Save as PNG to preserve transparency
        img.save(output_path, "PNG")
        print(f"OK -> {slug}.png")
        success_count += 1

    print("-" * 60)
    print(f"Complete! {success_count} succeeded, {failed_count} failed")
    print(f"Logos saved to: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
