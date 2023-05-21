
from enum import Enum
from pprint import pprint


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
        "leagues": "https://sportsapicdn-desktop.betking.com/api/feeds/prematch/en/4/{leagueid}/0/0"
    },
    "nairabet": {
        "leagues": "https://sports-api.nairabet.com/v2/events?country=NG&locale=en&group=g3&platform=desktop&sportId=SOCCER&competitionId={leagueid}&limit=10",
        "leaguesDNB": "https://sports-api.nairabet.com/v2/events?country=NG&locale=en&group=g3&platform=desktop&sportId=SOCCER&competitionId={leagueid}&marketId=DNB&limit=10"
    },
    "sportybet": {
        "leagues": [{"sportId":"sr:sport:1","marketId":"1,18,10,29,11,26,36,14","tournamentId":[[{"sr:tournament:1"}]]}]  # noqa: E231, E501
    }

}


# implement id's as enum
class Betid(Enum):
    PREMIERLEAGUE = 170880, 841, "EN_PR", 17
    CHAMPIONSHIP = 170881, 863, "EN_CH", 18
    LEAGUE_ONE = 995354, 909, "EN_L1", 24
    LEAGUE_TWO = 995355, 939, "EN_L2", 25
    BUNDESLIGA = 180923, 1007, "DE_BL", 35
    BUNDESLIGA_2 = 180924, 1025, "DE_B2", 44
    LALIGA = 180928, 1108, "ES_PL", 8
    LIGUE_1 = 950503, 1104, "FR_L1", 34
    LIGUE_2 = 958691, 1179, "FR_L2", 182
    SERIEA = 167856, 3775, "IT_SA", 23
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
        elif betting_site == 'nairabetDNB':
            endpoint_url = endpoints[betting_site]["leaguesDNB"].format(
                leagueid=self.nairabet_id
            )
        elif betting_site == 'sportybet':
            pprint(endpoints[betting_site]["leagues"])
            payload = endpoints[betting_site]["leagues"]
            payload[0]["tournamentId"][0][0] = "sr:tournament:{0}".format(self.sportybet_id)
            pprint(payload)
            return payload
        return endpoint_url
