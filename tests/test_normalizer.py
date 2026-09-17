"""The normalizer drops a malformed row with one warning and loads its tables once."""

import builtins
import logging
from collections import Counter
from pathlib import Path

from NaijaBet_Api.utils import normalizer
from NaijaBet_Api.utils.normalizer import (
    _load,
    _tables,
    bet9ja_match_normalizer,
    betking_match_normalizer,
    nairabet_match_normalizer,
)

LOGGER = "NaijaBet_Api.utils.normalizer"
TABLE_DIR = Path(normalizer.__file__).parent


def _rows(count: int) -> list[dict]:
    return [{"match": f"Team {i} - Other {i}", "league": "Premier League", "home": "1.5"} for i in range(count)]


def test_malformed_row_is_skipped_with_one_warning(caplog):
    rows = [{"match": "Arsenal - Chelsea"}, {"match": "postponed fixture"}, {"match": "Brentford - Everton"}]

    with caplog.at_level(logging.WARNING, logger=LOGGER):
        result = bet9ja_match_normalizer(rows)

    assert [row["match"] for row in result] == ["Arsenal - Chelsea", "Brentford - Everton"]
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "postponed fixture" in warnings[0].getMessage()


def test_tables_open_each_json_file_at_most_once(monkeypatch):
    _tables.cache_clear()
    _load.cache_clear()
    opened: Counter = Counter()
    real_open = builtins.open

    def counting_open(file, *args, **kwargs):
        if str(file).endswith(".json"):
            opened[Path(file).name] += 1
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", counting_open)

    result = bet9ja_match_normalizer(_rows(200))

    assert len(result) == 200
    assert set(opened) == {"bet9ja_normalizer.json", "betking_normalizer.json", "nairabet_normalizer.json"}
    assert max(opened.values()) == 1


def test_tables_open_each_json_file_at_most_once_across_sites(monkeypatch):
    _tables.cache_clear()
    _load.cache_clear()
    opened: Counter = Counter()
    real_open = builtins.open

    def counting_open(file, *args, **kwargs):
        if str(file).endswith(".json"):
            opened[Path(file).name] += 1
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", counting_open)

    bet9ja_result = bet9ja_match_normalizer(_rows(50))
    betking_result = betking_match_normalizer(_rows(50))

    assert len(bet9ja_result) == 50
    assert len(betking_result) == 50
    assert set(opened) == {"bet9ja_normalizer.json", "betking_normalizer.json", "nairabet_normalizer.json"}
    assert max(opened.values()) == 1


def test_own_table_wins_over_the_other_tables():
    # "LaLiga" maps to "La Liga" in every table; the bet9ja table is consulted first for bet9ja rows.
    assert bet9ja_match_normalizer([{"league": "LaLiga"}])[0]["league"] == "La Liga"
    assert _tables("bet9ja_normalizer.json").maps[0] is not _tables("nairabet_normalizer.json").maps[0]


def test_unknown_name_falls_through_at_debug(caplog):
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        result = nairabet_match_normalizer([{"match": "Zzyzx Rovers - Qqwx United"}])

    assert result[0]["match"] == "Zzyzx Rovers - Qqwx United"
    assert all(record.levelno == logging.DEBUG for record in caplog.records)
    assert len(caplog.records) == 2
