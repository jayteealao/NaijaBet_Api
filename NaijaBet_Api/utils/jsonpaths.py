from typing import Any, Mapping, Sequence
import jmespath


def bet9ja_league_path(json) -> Sequence[Mapping[Any, Any]]:

    """
    An helper function that cleans the endpoint returned json

    Args:
        json (dict): The json returned from the endpoint

    Returns:
        json (list(dict)): A list of dicts containing the league data in a more human readable format
    """

    search_string = ('D.E[*].{"match": DS, '
                     '"league": GN, '
                     '"time": STARTDATE, '
                     '"league_id": GID, '
                     '"match_id": ID, '
                     '"home": O.S_1X2_1 '
                     '"draw": O.S_1X2_X '
                     '"away": O.S_1X2_2 '
                     '"home_or_draw": O.S_DC_1X '
                     '"home_or_away": O.S_DC_12 '
                     '"draw_or_away": O.S_DC_X2 '
                     '}')

    expression = jmespath.compile(search_string)
    return expression.search(json)


def betking_league_path(json) -> Sequence[Mapping[Any, Any]]:

    """
    An helper function that cleans the endpoint returned json

    Args:
        json (dict): The json returned from the endpoint

    Returns:
        json (list(dict)): A list of dicts containing the league data in a more human readable format
    """

    search_string = ('AreaMatches[0].Items[*].{"match": ItemName, '
                     '"league": TournamentName, '
                     '"time": ItemDate, '
                     '"league_id": CategoryId, '
                     '"match_id": ItemID, '
                     '"home": OddsCollection[0].MatchOdds[0].Outcome.OddOutcome '
                     '"draw": OddsCollection[0].MatchOdds[1].Outcome.OddOutcome '
                     '"away": OddsCollection[0].MatchOdds[2].Outcome.OddOutcome '
                     '"home_or_draw": OddsCollection[1].MatchOdds[0].Outcome.OddOutcome '
                     '"home_or_away": OddsCollection[1].MatchOdds[1].Outcome.OddOutcome '
                     '"draw_or_away": OddsCollection[1].MatchOdds[2].Outcome.OddOutcome '
                     '}')

    expression = jmespath.compile(search_string)
    return expression.search(json)


def nairabet_league_path(json) -> Sequence[Mapping[Any, Any]]:

    """
    An helper function that cleans the endpoint returned json

    Args:
        json (dict): The json returned from the endpoint

    Returns:
        json (list(dict)): A list of dicts containing the league data in a more human readable format
    """

    search_string = ('data[*].{"match": eventName, '
                     '"league": category3Name, '
                     '"time": eventStart, '
                     '"league_id": category3Id, '
                     '"match_id": eventId, '
                     '"home": eventGames[0].outcomes[0].outcomeOdds '
                     '"draw": eventGames[0].outcomes[1].outcomeOdds '
                     '"away": eventGames[0].outcomes[2].outcomeOdds '
                     '"home_or_draw": eventGames[1].outcomes[0].outcomeOdds '
                     '"home_or_away": eventGames[1].outcomes[1].outcomeOdds '
                     '"draw_or_away": eventGames[1].outcomes[2].outcomeOdds '
                     '}')

    expression = jmespath.compile(search_string)
    return expression.search(json)
