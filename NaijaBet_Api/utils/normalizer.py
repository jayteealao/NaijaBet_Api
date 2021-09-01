import json
import re
from typing import ChainMap
import arrow
from pathlib import Path
import difflib
from NaijaBet_Api.utils.logger import get_logger

logger = get_logger(__name__)


def match_normalizer(list, pathstr: str):
    path = Path(__file__).parent / pathstr
    if list is None:
        return {}
    data = list[:]

    def helper(string):
        with open(path, "r") as f:
            normalizer = json.load(f)
            try:
                return normalizer[string]
            except KeyError:
                logger.warning(f"{string} not found in {pathstr} normalizer")
                path_b9 = Path(__file__).parent / "bet9ja_normalizer.json"
                path_bk = Path(__file__).parent / "betking_normalizer.json"
                path_nb = Path(__file__).parent / "nairabet_normalizer.json"

                map = ChainMap(
                    json.load(open(path_b9, "r")), json.load(open(path_bk, "r")), json.load(open(path_nb, "r")))
                try:
                    return map[string]
                except KeyError:
                    logger.warning(f"{string} not found in normalizer")
                    res = difflib.get_close_matches(string, map.keys(), 1, 0.8)
                    logger.info('found possible matches {res}')
                    return map[res[0]]


    for event in data:
        teams = event["match"]
        home, away = re.split(r"\s-\s", teams, maxsplit=1)
        home = helper(home.strip())
        away = helper(away.strip())
        event["match"] = "{0} - {1}".format(home, away)
        event["time"] = arrow.get(event["time"]).int_timestamp
        event['league'] = helper(event['league'])

    return data


def bet9ja_match_normalizer(list):
    return match_normalizer(list, "bet9ja_normalizer.json")


def nairabet_match_normalizer(list):
    return match_normalizer(list, "nairabet_normalizer.json")


def betking_match_normalizer(list):
    return match_normalizer(list, "betking_normalizer.json")
