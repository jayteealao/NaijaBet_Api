import difflib
import json
import logging
import re
from collections import ChainMap
from functools import lru_cache
from pathlib import Path

import arrow

logger = logging.getLogger(__name__)

_TABLES = ("bet9ja_normalizer.json", "betking_normalizer.json", "nairabet_normalizer.json")
_ODDS_FIELDS = ("home", "draw", "away", "home_or_draw", "home_or_away", "draw_or_away")


@lru_cache(maxsize=None)
def _load(name: str) -> dict:
    with open(Path(__file__).parent / name, "r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=None)
def _tables(pathstr: str) -> ChainMap:
    """The name tables for one bookmaker: its own file first, then the other two.

    The files are package data and load once per process; call ``_tables.cache_clear()``
    after editing one at runtime.
    """
    return ChainMap(_load(pathstr), *(_load(name) for name in _TABLES if name != pathstr))


def _canonical(name: str, tables: ChainMap) -> str:
    if name in tables:
        return tables[name]
    close = difflib.get_close_matches(name, tables.keys(), 1, 0.8)
    logger.debug("%s not in the normalizer tables; close matches %s", name, close)
    return tables[close[0]] if close else name


def match_normalizer(list, pathstr: str):
    if list is None:
        return {}
    tables = _tables(pathstr)
    data = []

    for event in list:
        teams = event.get("match", None)
        if teams is not None:
            parts = re.split(r"\s-\s", teams, maxsplit=1)
            if len(parts) != 2:
                logger.warning("skipping row with unparseable match %r", teams)
                continue
            home, away = (_canonical(part.strip(), tables) for part in parts)
            event["match"] = "{0} - {1}".format(home, away)

        time = event.get("time", None)
        if time is not None:
            event["time"] = arrow.get(event["time"]).int_timestamp

        league = event.get("league", None)
        if league is not None:
            event["league"] = _canonical(league, tables)

        # Convert odds fields from strings to floats
        for field in _ODDS_FIELDS:
            if field in event and event[field] is not None:
                try:
                    event[field] = float(event[field])
                except (ValueError, TypeError):
                    logger.warning("Could not convert %s=%r to float", field, event[field])
        data.append(event)

    return data


def bet9ja_match_normalizer(list):
    return match_normalizer(list, "bet9ja_normalizer.json")


def nairabet_match_normalizer(list):
    return match_normalizer(list, "nairabet_normalizer.json")


def betking_match_normalizer(list):
    return match_normalizer(list, "betking_normalizer.json")
