# NaijaBet-Api

[![publish-pypi](https://github.com/jayteealao/NaijaBet_Api/actions/workflows/py-build.yml/badge.svg?branch=release)](https://github.com/jayteealao/NaijaBet_Api/actions/workflows/py-build.yml)

A python library that provides access to the odds data of Nigeria's major betting sites.

It provides access to Bet9ja, Betking and Nairabet's 1X2 and doublechance soccer odds.

## Basic Usage

Import the requested bookmaker:

```python
from NaijaBet_Api.bookmakers import bet9ja, betking, nairabet
```

Access specific bookmaker

```python
from NaijaBet_Api.bookmakers import bet9ja

b9 = bet9ja.Bet9ja()
```

Obtain League data:  
*note: in order to access a specific league you need to provide the league as an argument via the **Betid Enum Class***

```python
from NaijaBet_Api.bookmakers import bet9ja
from NaijaBet_Api.id import Betid

b9 = bet9ja.Bet9ja()
b9.get_league(Betid.PREMIERLEAGUE)
```

Obtain all league data:

```python
from NaijaBet_Api.bookmakers import bet9ja
from NaijaBet_Api.id import Betid

b9 = bet9ja.Bet9ja()
b9.get_all()
```

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
