#!/usr/bin/env python3
"""
Script to populate coordinates for NCAA schools in the team data file.

This script reads the existing NCAA team data and updates any schools
that have coordinates set to {x: 0, y: 0} with actual geographic coordinates.
"""

import sys
import os
import json
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from hoopland.data.coordinate_utils import get_school_coordinates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main function to populate NCAA coordinates."""
    ncaa_data_file = "src/hoopland/data/ncaa_team_data.json"

    # Load current data
    try:
        with open(ncaa_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"NCAA data file not found: {ncaa_data_file}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing NCAA data file: {e}")
        return 1

    updated_count = 0
    total_schools = len(data)

    logger.info(f"Processing {total_schools} schools...")

    # Update coordinates for each school
    for school_key, school_data in data.items():
        school_name = school_data.get('school', '')
        current_coords = school_data.get('location', {})

        # Only update if coordinates are missing (x=0, y=0)
        if current_coords.get('x') == 0 and current_coords.get('y') == 0:
            coords = get_school_coordinates(school_name)
            if coords:
                school_data['location'] = coords
                updated_count += 1
                logger.info(f"Updated {school_name}: {coords}")
            else:
                logger.warning(f"No coordinates found for {school_name}")

    # Save updated data
    try:
        with open(ncaa_data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving updated data: {e}")
        return 1

    logger.info(f"Successfully updated coordinates for {updated_count}/{total_schools} schools")
    return 0


if __name__ == "__main__":
    sys.exit(main())


