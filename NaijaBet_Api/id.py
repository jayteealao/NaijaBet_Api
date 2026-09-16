from enum import Enum

from NaijaBet_Api.utils.altenar import EVENTS_URL

endpoints = {
    "bet9ja": {
        "sports": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetSports?DISP=0&v_cache_version=1.164.0.135",
        "leaguetry": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetEventsInCouponV2?SCHID=492&DISP=0&MKEY=1&v_cache_version=1.169.1.135",
        "leagues": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetEventsInGroupV2?GROUPID={leagueid}&DISP=0&GROUPMARKETID=1&matches=true",  # noqa: E501
        "live": "https://sports.bet9ja.com/desktop/feapi/PalimpsestLiveAjax/GetLiveEventsV3?v_cache_version=1.164.0.135",  # noqa: E501
        "markets": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetGroupMarketsById?GROUPID=170880",
        "matches": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetEvent?EVENTID=137750929&v_cache_version=1.164.0.135",  # noqa: E501
    },
    "betking": {
        "popular": "https://sportsapicdn-desktop.betking.com/api/feeds/prematch/mostpopularsports/en/1/5/15/",
        "leagues": "https://sportsapicdn-desktop.betking.com/api/feeds/prematch/en/4/{leagueid}/0/0",
    },
    "nairabet": {
        # Nairabet's sportsbook is an Altenar widget; one GetEvents body carries the 1X2, double-chance,
        # and draw-no-bet markets for a competition (champIds).
        "leagues": EVENTS_URL,
        "leaguesDNB": EVENTS_URL,
    },
}


# One member per league: (bet9ja group id, betking tournament id, nairabet/Altenar champ id, sportybet id)
class Betid(Enum):
    PREMIERLEAGUE = 170880, 20000841, 2936, 17
    CHAMPIONSHIP = 170881, 20000863, 2937, 18
    LEAGUE_ONE = 995354, 20000909, 2947, 24
    LEAGUE_TWO = 995355, 20000939, 2946, 25
    BUNDESLIGA = 180923, 20001007, 2950, 35
    BUNDESLIGA_2 = 180924, 20001025, 2954, 44
    LALIGA = 180928, 20001108, 2941, 8
    LIGUE_1 = 950503, 20001104, 2943, 34
    LIGUE_2 = 958691, 20001179, 3143, 182
    SERIEA = 167856, 20003775, 2942, 23

    def __init__(self, bet9ja_id, betking_id, nairabet_id, sportybet_id):
        self.bet9ja_id = bet9ja_id
        self.betking_id = betking_id
        self.nairabet_id = nairabet_id
        self.sportybet_id = sportybet_id

    def to_endpoint(self, betting_site: str) -> str:
        """Return the league URL for one of the three bookmakers.

        Raises:
            ValueError: ``betting_site`` is not ``bet9ja``, ``betking``, or ``nairabet``.
        """
        ids = {"bet9ja": self.bet9ja_id, "betking": self.betking_id, "nairabet": self.nairabet_id}
        if betting_site not in ids:
            raise ValueError(f"unknown betting site {betting_site!r}; expected one of bet9ja, betking, nairabet")
        return endpoints[betting_site]["leagues"].format(leagueid=ids[betting_site])
