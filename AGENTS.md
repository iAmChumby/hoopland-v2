# Hoopland Development Guide

## Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_hoopland.py

# Run single test
pytest tests/test_hoopland.py::test_normalization

# Run with verbose output
pytest -v
```

### Running the Application
```bash
# Generate NBA league
python src/hoopland/cli.py --league nba --year 2003

# Generate draft class
python src/hoopland/cli.py --league draft --year 2003

# With debug logging
python src/hoopland/cli.py --league nba --year 2003 --debug
```

## Code Style

### Imports
- Use relative imports within the package: `from .workflows import ...`
- Group imports: standard library, third-party, local
- Avoid absolute imports like `from src.hoopland...`

### Formatting
- No comments in code (per project style)
- snake_case for functions/variables
- PascalCase for classes
- Type hints required for function signatures
- Maximum line length: follow existing patterns

### Error Handling
- Use try/except blocks for external operations (API calls, DB)
- Log errors with `logger.error()` or `logger.exception()`
- Use `sys.exit(1)` for CLI failures

### Types & Structures
- Use dataclasses for data structures (`@dataclass`)
- Use `Optional[Type]` for nullable fields
- Use `Dict[str, Any]` for flexible dictionaries

### Logging
- Create module-level logger: `logger = logging.getLogger(__name__)`
- Use appropriate levels: DEBUG, INFO, WARNING, ERROR
- Log exceptions with `logger.exception()` for stack traces

### Testing
- Use pytest (not unittest)
- Mock external dependencies (APIs, DB)
- Use fixtures for test setup
- Test file naming: `test_*.py`
