import json
import re
import arrow
from pathlib import Path


def match_normalizer(list, path: Path):
    data = list[:]

    def helper(string):
        with open(path.absolute(), "r") as f:
            normalizer = json.load(f)
            res = normalizer[string]
            return res

    for event in data:
        teams = event["match"]
        home, away = re.split(r"\s-\s", teams, maxsplit=1)
        home = helper(home.strip())
        away = helper(away.strip())
        event["match"] = "{0} - {1}".format(home, away)
        event["time"] = arrow.get(event["time"]).int_timestamp

    return data


def bet9ja_match_normalizer(list):
    return match_normalizer(list, Path("Naijabet_Api/utils/bet9ja_normalizer.json"))


def nairabet_match_normalizer(list):
    return match_normalizer(list, Path("Naijabet_Api/utils/nairabet_normalizer.json"))


def betking_match_normalizer(list):
    return match_normalizer(list, Path("Naijabet_Api/utils/betking_normalizer.json"))
