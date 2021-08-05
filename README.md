# NaijaBet-Api

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

## TODO

- [ ] Add Sportybet
- [ ] Add all soccer leagues
- [ ] Add access to available bookmaker odds for specific matches
