# Testing Guide

## Running Tests
This project uses `pytest` for testing.

To run the full suite:
```bash
pytest
```

To run with coverage report:
```bash
pytest --cov=src
```

## Test Structure
- `tests/`: Contains all test files.
- `tests/conftest.py`: Shared fixtures (planned).
- `tests/test_integration.py`: End-to-end integration tests (generation logic).
- `tests/test_appearance_logic.py`: Logic tests for CV and appearance matching.

## Configuration
Testing is configured in `pyproject.toml`.
