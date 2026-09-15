from NaijaBet_Api.utils.jsonpaths import betking_validator


def test_betking_validator_returns_empty_list_for_empty_area_matches():
    live_body = {
        "AreaMatches": [],
        "Areas": [{"AreaID": 0, "AreaName": None, "AreaOrder": 0, "MarketCount": 0}],
        "Regions": [],
        "TotalNoOfItems": 0,
    }

    result = betking_validator(live_body)

    assert result == []


def test_betking_validator_returns_none_for_foreign_body():
    foreign_body = {"foo": 1}

    result = betking_validator(foreign_body)

    assert result is None


def test_betking_validator_single_area_behaviour_unchanged():
    body = {
        "AreaMatches": [
            {
                "Items": [
                    {
                        "ItemName": "A - B",
                        "TournamentName": "T",
                        "ItemDate": "2026-09-20T15:00:00",
                        "CategoryId": 1,
                        "ItemID": 2,
                        "OddsCollection": [
                            {
                                "MatchOdds": [
                                    {"Outcome": {"OddOutcome": 2.1}},
                                    {"Outcome": {"OddOutcome": 3.4}},
                                    {"Outcome": {"OddOutcome": 3.2}},
                                ]
                            },
                            {
                                "MatchOdds": [
                                    {"Outcome": {"OddOutcome": 1.3}},
                                    {"Outcome": {"OddOutcome": 1.27}},
                                    {"Outcome": {"OddOutcome": 1.65}},
                                ]
                            },
                        ],
                    }
                ]
            }
        ]
    }

    result = betking_validator(body)

    assert len(result) == 1
    row = result[0]
    assert set(row.keys()) == {
        "match",
        "league",
        "time",
        "league_id",
        "match_id",
        "home",
        "draw",
        "away",
        "home_or_draw",
        "home_or_away",
        "draw_or_away",
    }
    assert row["home"] == 2.1
