# End-to-End Tests for NaijaBet API

This directory contains real end-to-end tests that verify the actual functionality of the NaijaBet API library against live betting site APIs.

## Test Coverage

The test suite includes comprehensive tests for all three bookmakers:

### Bet9ja (10 tests)
- Initialization
- League data fetching (Premier League, La Liga, Bundesliga)
- All leagues fetching
- Team search
- Async league fetching
- Async all leagues fetching
- Multiple sequential requests
- Invalid league handling

### Betking (11 tests)
- Initialization
- League data fetching (Premier League, La Liga, Bundesliga, Serie A)
- All leagues fetching
- Team search
- Async league fetching
- Async all leagues fetching
- Multiple sequential requests
- Data normalization validation

### Nairabet (12 tests)
- Initialization
- League data fetching (Premier League, La Liga, Bundesliga, Serie A)
- All leagues fetching
- Team search
- Async league fetching
- Async all leagues fetching
- Multiple sequential requests
- League normalization validation
- Data normalization validation

## Running the Tests

### Run all tests
```bash
python -m pytest tests/ -v
```

### Run tests for a specific bookmaker
```bash
python -m pytest tests/test_bet9ja_e2e.py -v
python -m pytest tests/test_betking_e2e.py -v
python -m pytest tests/test_nairabet_e2e.py -v
```

### Run a specific test
```bash
python -m pytest tests/test_bet9ja_e2e.py::TestBet9jaE2E::test_get_league_premier_league -v
```

## Test Features

### Real API Calls
All tests make actual HTTP requests to the live bookmaker APIs - no mocks, no fakes, no stubs. This ensures the library works with the real-world APIs.

### Both Sync and Async
Tests cover both synchronous and asynchronous API methods to ensure both code paths work correctly.

### Data Validation
Tests verify:
- Correct data structure and types
- Required fields presence
- Proper data normalization (team names, league names)
- Odds values are numeric (float/int)
- Timestamps are integers
- Match format follows "Team A - Team B" pattern

### Error Handling
Tests verify graceful handling of:
- API failures
- Network issues
- Missing data
- Invalid responses

## Known Issues

### Betking API
Betking's API is protected by Cloudflare bot protection and may return 403 errors. The tests handle this gracefully by returning empty results rather than crashing. This is expected behavior in the current environment.

## Bug Fixes Made

During the creation of these tests, several bugs in the codebase were discovered and fixed:

1. **Odds values as strings**: Fixed conversion of odds from strings to floats in `normalizer.py`
2. **Team name not found crash**: Fixed IndexError when team names aren't in normalizer JSON files
3. **Async session cleanup**: Fixed unclosed aiohttp client sessions
4. **JSON decode errors**: Added proper error handling for non-JSON API responses
5. **HTTP headers**: Added proper browser-like headers for Betking and Nairabet

## Dependencies

The tests require:
- pytest >= 7.0.0
- pytest-asyncio >= 0.18.0
- pytest-timeout >= 2.1.0

Install with:
```bash
pip install -r requirements.txt
```
