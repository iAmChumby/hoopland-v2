
import sys
import os
import logging

logging.basicConfig(level=logging.DEBUG)

# Ensure src is in path
sys.path.append('src')

from hoopland.blocks.generator import Generator

def test_generation():
    print("Initializing Generator...")
    gen = Generator()
    
    year = "2003"
    print(f"Generating League for {year}...")
    league = gen.generate_league(year)
    
    filename = f"NBA_{year}_League.txt"
    print(f"Saving to {filename}...")
    gen.to_json(league, filename)
    
    output_path = os.path.join("output", year, filename)
    if os.path.exists(output_path):
        print(f"SUCCESS: File created at {output_path}")
        # Print first few lines to verify content
        with open(output_path, 'r') as f:
            print(f.read(500))
    else:
        print(f"FAILURE: File not found at {output_path}")

if __name__ == "__main__":
    test_generation()
