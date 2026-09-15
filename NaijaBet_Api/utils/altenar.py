"""Row construction for the Altenar widget API that serves Nairabet's sportsbook.

One ``GetEvents`` body is normalized: ``events`` reference ``markets`` by id, ``markets``
reference ``odds`` by id, and ``competitors`` and ``champs`` are looked up by id. jmespath
has no join, so the eleven-key rows are built here with plain dict lookups.
"""

import logging

logger = logging.getLogger(__name__)

WIDGET_HOST = "https://sb2frontend-altenar2.biahosted.com"
WIDGET_QUERY = "culture=en-GB&timezoneOffset=-60&integration=nairabet&deviceType=1&numFormat=en-GB&countryCode=NG"
EVENTS_URL = f"{WIDGET_HOST}/api/widget/GetEvents?{WIDGET_QUERY}&champIds={{leagueid}}"
MENU_URL = f"{WIDGET_HOST}/api/widget/GetTopSportMenu?{WIDGET_QUERY}"

# Row key -> (market typeId, odd typeId). typeId 1 is 1x2, typeId 10 is double chance.
ODD_BY_KEY = {
    "home": (1, 1),
    "draw": (1, 2),
    "away": (1, 3),
    "home_or_draw": (10, 9),
    "home_or_away": (10, 10),
    "draw_or_away": (10, 11),
}


def _prices(event: dict, markets: dict, odds: dict) -> dict | None:
    """Return the six prices of one event, or None when any of them is missing."""
    found: dict[tuple[int, int], float] = {}
    for market_id in event["marketIds"]:
        market = markets.get(market_id)
        if market is None or market["typeId"] not in (1, 10):
            continue
        for odd_id in market["oddIds"]:
            odd = odds.get(odd_id)
            if odd is not None:
                found.setdefault((market["typeId"], odd["typeId"]), odd["price"])
    prices = {key: found.get(pair) for key, pair in ODD_BY_KEY.items()}
    if any(price is None for price in prices.values()):
        return None
    return prices


def rows_from_get_events(body: dict) -> list[dict]:
    """Turn one GetEvents body into rows with the keys the other bookmakers carry.

    An event without a complete 1x2 and double-chance pair is skipped. A body without the
    expected top-level keys raises KeyError, which the base class reports as a parse error.
    """
    markets = {market["id"]: market for market in body["markets"]}
    odds = {odd["id"]: odd for odd in body["odds"]}
    competitors = {competitor["id"]: competitor["name"] for competitor in body["competitors"]}
    champs = {champ["id"]: champ["name"] for champ in body["champs"]}
    rows = []
    for event in body["events"]:
        prices = _prices(event, markets, odds)
        if prices is None or len(event["competitorIds"]) < 2:
            logger.debug("skipping event %s: incomplete markets or competitors", event.get("id"))
            continue
        home, away = (competitors[competitor_id] for competitor_id in event["competitorIds"][:2])
        rows.append(
            {
                "match": f"{home} - {away}",
                "league": champs[event["champId"]],
                "time": event["startDate"],
                "league_id": event["champId"],
                "match_id": event["id"],
                **prices,
            }
        )
    return rows
