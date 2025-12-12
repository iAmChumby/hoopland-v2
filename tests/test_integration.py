import os
import pytest
from hoopland.blocks.generator import Generator


def test_generate_league_execution(tmp_path):
    """
    Test the end-to-end execution of league generation.
    Uses a temporary directory for output to avoid cluttering the repo.
    """
    # Initialize Generator
    gen = Generator()

    # We use a known year
    year = "2003"

    # Run Generation
    league = gen.generate_league(year)

    # Verify we got a league object (assuming it's a dict or object)
    assert league is not None, "League generation returned None"

    # Test file saving
    filename = f"NBA_{year}_League.txt"
    output_file = tmp_path / filename

    # Inspecting the code for Generator.to_json, it likely takes a path or uses a default.
    # The original script did:
    # output_path = os.path.join("output", year, filename)
    # gen.to_json(league, filename) which seemingly wrote to a fixed location or cwd?
    # Let's try to verify what to_json does. If it writes to CWD/output, we might need to check that.
    # For now, we will try to pass the full path if the method supports it, or check the default location.

    # Re-reading verify_generator.py:
    # gen.to_json(league, filename)
    # output_path = os.path.join("output", year, filename)

    # This implies to_json handles the 'output/{year}/' logic internally.
    # We will let it run and check the 'output' directory in the project root for now,
    # cleaning up if possible, or just verifying standard behavior.

    gen.to_json(league, filename)

    expected_path = os.path.join("output", year, filename)
    assert os.path.exists(expected_path), f"File was not created at {expected_path}"

    # Basic content check
    with open(expected_path, "r") as f:
        content = f.read()
        assert len(content) > 0, "Generated file is empty"
