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


def bet9ja_find_team(json, team: str) -> Sequence[Mapping[Any, Any]]:

    search_string = '[?contains(&match, {club})]'.format(club=team)
    print(search_string)
    expression = jmespath.compile(search_string)
    return expression.search(json)
