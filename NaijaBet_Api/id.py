from enum import Enum


endpoints = {
    "bet9ja": {
        "sports": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetSports?DISP=0&v_cache_version=1.164.0.135",
        "leagues": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetEventsInGroupV2?GROUPID={leagueid}&DISP=0&GROUPMARKETID=1&matches=true",  # noqa: E501
        "live": "https://sports.bet9ja.com/desktop/feapi/PalimpsestLiveAjax/GetLiveEventsV3?v_cache_version=1.164.0.135",  # noqa: E501
        "markets": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetGroupMarketsById?GROUPID=170880",
        "matches": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetEvent?EVENTID=137750929&v_cache_version=1.164.0.135",  # noqa: E501
    }
}


# implement id's as enum
class Betid(Enum):
    PREMIERLEAGUE = 170880
    CHAMPIONSHIP = 170881
    LEAGUE_ONE = 995354
    LEAGUE_TWO = 995355
    BUNDESLIGA = 180923
    BUNDESLIGA_2 = 180924
    LALIGA = 180928
    LIGUE_1 = 950503
    LIGUE_2 = 958691

    def __init__(self, bet9ja_id):
        self.bet9ja_id = bet9ja_id

    def to_endpoint(self, betting_site):
        if betting_site == "bet9ja":
            endpoint_url = endpoints[betting_site]["leagues"].format(
                leagueid=self.bet9ja_id
            )
            return endpoint_url
