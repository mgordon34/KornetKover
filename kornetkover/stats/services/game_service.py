from datetime import datetime
from typing import List

from kornetkover.stats.models.game import Game

class GameService(object):

    def __init__(self, db):
        self.db = db

    def get_games_for_date(self, date: datetime.date) -> List[Game]:
        sql = f"""SELECT id, home_index, away_index, date
                 FROM games
                 WHERE date=Date('{date}')"""

        res = self.db.execute_query(sql)
        if not res:
            return []

        games = []
        for game in res:
            games.append(Game(*game))

        return games
