
from enum import Enum
from pprint import pprint


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
    },
    "sportybet": {
        "leagues": [{"sportId":"sr:sport:1","marketId":"1,18,10,29,11,26,36,14","tournamentId":[[{"sr:tournament:1"}]]}]  # noqa: E231, E501
    }

}


# implement id's as enum
class Betid(Enum):
    PREMIERLEAGUE = 170880, 841, 135975, 17
    CHAMPIONSHIP = 170881, 863, 135859, 18
    LEAGUE_ONE = 995354, 909, 135795, 24
    LEAGUE_TWO = 995355, 939, 135845, 25
    BUNDESLIGA = 180923, 1007, 135807, 35
    BUNDESLIGA_2 = 180924, 1025, 136023, 44
    LALIGA = 180928, 1108, 136013, 8
    LIGUE_1 = 950503, 1104, 135922, 34
    LIGUE_2 = 958691, 1179, 135910, 182
    SERIEA = 167856, 3775, 135763, 23
    # replace betkings laliga id

    def __init__(self, bet9ja_id, betking_id, nairabet_id, sportybet_id):
        self.bet9ja_id = bet9ja_id
        self.betking_id = betking_id
        self.nairabet_id = nairabet_id
        self.sportybet_id = sportybet_id

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
        elif betting_site == 'sportybet':
            pprint(endpoints[betting_site]["leagues"])
            payload = endpoints[betting_site]["leagues"]
            payload[0]["tournamentId"][0][0] = "sr:tournament:{0}".format(self.sportybet_id)
            pprint(payload)
            return payload
        return endpoint_url
