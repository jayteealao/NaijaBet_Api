# NaijaBet-Api

[![publish-pypi](https://github.com/jayteealao/NaijaBet_Api/actions/workflows/py-build.yml/badge.svg?branch=release)](https://github.com/jayteealao/NaijaBet_Api/actions/workflows/py-build.yml)

A python library that provides access to the odds data of Nigeria's major betting sites.

It provides access to Bet9ja, Betking and Nairabet's 1X2 and doublechance soccer odds.

## Basic Usage

### Quick Start (Bet9ja & Nairabet)

These work without any additional setup:

```python
from NaijaBet_Api.bookmakers import Bet9ja, Nairabet
from NaijaBet_Api.id import Betid

# Initialize
bet9ja = Bet9ja()
nairabet = Nairabet()

# Get Premier League odds
bet9ja_odds = bet9ja.get_league(Betid.PREMIERLEAGUE)
nairabet_odds = nairabet.get_league(Betid.PREMIERLEAGUE)

# Get all leagues
all_odds = bet9ja.get_all()
```

### Betking (Requires Playwright)

⚠️ **Betking is protected by Cloudflare** - requires browser automation:

```python
# Install first: pip install playwright && playwright install chromium

from NaijaBet_Api.bookmakers import BetkingPlaywright
from NaijaBet_Api.id import Betid

# Use context manager (recommended)
with BetkingPlaywright() as betking:
    data = betking.get_league(Betid.PREMIERLEAGUE)
    print(f"Got {len(data)} matches")
```

See [`BETKING_BROWSER_AUTOMATION.md`](BETKING_BROWSER_AUTOMATION.md) for complete guide.
See [`examples/betking_playwright_example.py`](examples/betking_playwright_example.py) for full examples.

The get_all and get_league methods return a list of dicts  
example:

```json
[{'away': 1.92,
  'draw': 3.75,
  'draw_or_away': 1.28,
  'home': 4.0,
  'home_or_away': 1.3,
  'home_or_draw': 1.89,
  'league': 'Premier League',
  'league_id': 135975,
  'match': 'Brentford FC - Arsenal FC',
  'match_id': 4467373,
  'time': 1628881200000},
 {'away': 5.6,
  'draw': 4.8,
  'draw_or_away': 2.47,
  'home': 1.54,
  'home_or_away': 1.21,
  'home_or_draw': 1.18,
  'league': 'Premier League',
  'league_id': 135975,
  'match': 'Manchester United FC - Leeds United',
  'match_id': 4467299,
  'time': 1628940600000},]
```

## TODO

- [ ] Add Sportybet
- [ ] Add all soccer leagues
- [ ] Add access to available bookmaker odds for specific matches
