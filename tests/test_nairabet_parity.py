"""Nairabet rows carry the same eleven keys, with the same types, as the Bet9ja rows."""

import copy

import pytest

from NaijaBet_Api import ResponseParseError
from NaijaBet_Api.id import Betid
from NaijaBet_Api.utils.altenar import rows_from_get_events

ODDS_KEYS = ["home", "draw", "away", "home_or_draw", "home_or_away", "draw_or_away"]


def test_rows_match_bet9ja_keys_and_types(nairabet_stub, stub, league_routes):
    league_routes()
    bet9ja_row = stub().get_league(Betid.PREMIERLEAGUE)[0]

    rows = nairabet_stub().get_league(Betid.PREMIERLEAGUE)

    assert len(rows) == 3
    for row in rows:
        assert set(row) == set(bet9ja_row)
        assert {key: type(value) for key, value in row.items()} == {
            key: type(value) for key, value in bet9ja_row.items()
        }


def test_first_row_values(nairabet_stub):
    row = nairabet_stub().get_league(Betid.PREMIERLEAGUE)[0]

    assert row["match"] == "Brentford - Chelsea"
    assert row["league"] == "Premier League"
    assert row["league_id"] == 2936
    assert row["match_id"] == 17162768
    assert row["time"] == 1789758000
    assert [row[key] for key in ODDS_KEYS] == [2.94, 3.93, 2.29, 1.6, 1.25, 1.4]


def test_requested_url_carries_the_champ_id(nairabet_stub, httpserver):
    nairabet_stub().get_league(Betid.BUNDESLIGA)

    queries = [request.query_string.decode() for request, _ in httpserver.log if request.path == "/GetEvents"]
    assert queries == ["champIds=2950"]


def test_empty_events_body_returns_empty_list(nairabet_stub, httpserver, nairabet_payload):
    empty = {key: [] if isinstance(value, list) else value for key, value in nairabet_payload.items()}
    httpserver.clear_all_handlers()
    httpserver.expect_request("/GetTopSportMenu").respond_with_json({})
    httpserver.expect_request("/GetEvents").respond_with_json(empty)

    assert nairabet_stub().get_league(Betid.PREMIERLEAGUE) == []


def test_foreign_body_raises_parse_error(nairabet_stub, httpserver):
    httpserver.clear_all_handlers()
    httpserver.expect_request("/GetTopSportMenu").respond_with_json({})
    httpserver.expect_request("/GetEvents").respond_with_json({"data": []})

    with pytest.raises(ResponseParseError) as info:
        nairabet_stub().get_league(Betid.PREMIERLEAGUE)
    assert info.value.bookmaker == "nairabet"


def _drop_market(payload: dict, event_index: int, type_id: int) -> dict:
    body = copy.deepcopy(payload)
    event = body["events"][event_index]
    markets = {market["id"]: market for market in body["markets"]}
    event["marketIds"] = [market_id for market_id in event["marketIds"] if markets[market_id]["typeId"] != type_id]
    return body


def test_event_without_double_chance_market_is_skipped(nairabet_payload):
    body = _drop_market(nairabet_payload, 1, 10)

    rows = rows_from_get_events(body)

    assert [row["match_id"] for row in rows] == [body["events"][0]["id"], body["events"][2]["id"]]


def test_event_with_a_missing_odd_is_skipped(nairabet_payload):
    body = copy.deepcopy(nairabet_payload)
    first_market = body["events"][0]["marketIds"][0]
    market = next(market for market in body["markets"] if market["id"] == first_market)
    market["oddIds"] = market["oddIds"][:2]

    rows = rows_from_get_events(body)

    assert len(rows) == 2
    assert body["events"][0]["id"] not in {row["match_id"] for row in rows}


def test_league_name_comes_from_champs(nairabet_payload):
    body = copy.deepcopy(nairabet_payload)
    body["champs"][0]["name"] = "Renamed League"

    assert {row["league"] for row in rows_from_get_events(body)} == {"Renamed League"}
