import json
import re
import arrow
from pathlib import Path


def match_normalizer(list, path: str):
    path = Path(__file__).parent / path
    if list is None:
        return {}
    data = list[:]

    def helper(string):
        with open(path, "r") as f:
            normalizer = json.load(f)
            return normalizer[string]

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
