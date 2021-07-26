
from enum import Enum


endpoints = {
    "bet9ja": {
        "sports": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetSports?DISP=0&v_cache_version=1.164.0.135",
        "leagues": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetEventsInGroupV2?GROUPID={leagueid}&DISP=0&GROUPMARKETID=1&matches=true",  # noqa: E501
        "live": "https://sports.bet9ja.com/desktop/feapi/PalimpsestLiveAjax/GetLiveEventsV3?v_cache_version=1.164.0.135",  # noqa: E501
        "markets": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetGroupMarketsById?GROUPID=170880",
        "matches": "https://sports.bet9ja.com/desktop/feapi/PalimpsestAjax/GetEvent?EVENTID=137750929&v_cache_version=1.164.0.135",  # noqa: E501
    },
    "betking": {
        "popular": "https://sportsapicdn-desktop.betking.com/api/feeds/prematch/mostpopularsports/en/1/5/15/",
        "leagues": "https://sportsapicdn-desktop.betking.com/api/feeds/prematch/en/4/{leagueid}/0/0"
    },
    "nairabet": {
        "leagues": "https://www.nairabet.com/rest/market/categories/multi/{leagueid}/events"
    }

}


# implement id's as enum
class Betid(Enum):
    PREMIERLEAGUE = 170880, 841, 135975
    CHAMPIONSHIP = 170881, 863, 135859
    LEAGUE_ONE = 995354, 909, 135795
    LEAGUE_TWO = 995355, 939, 135845
    BUNDESLIGA = 180923, 1007, 135807
    BUNDESLIGA_2 = 180924, 1025, 136023
    LALIGA = 180928, 1107, 136013
    LIGUE_1 = 950503, 1104, 135922
    LIGUE_2 = 958691, 1179, 135910
    SERIEA = 167856, 3775, 135763

    def __init__(self, bet9ja_id, betking_id, nairabet_id):
        self.bet9ja_id = bet9ja_id
        self.betking_id = betking_id
        self.nairabet_id = nairabet_id

    def to_endpoint(self, betting_site):
        if betting_site == 'bet9ja':
            endpoint_url = endpoints[betting_site]["leagues"].format(
                leagueid=self.bet9ja_id
            )
        elif betting_site == 'betking':
            endpoint_url = endpoints[betting_site]["leagues"].format(
                leagueid=self.betking_id
            )
        elif betting_site == 'nairabet':
            endpoint_url = endpoints[betting_site]["leagues"].format(
                leagueid=self.nairabet_id
            )
        return endpoint_url
