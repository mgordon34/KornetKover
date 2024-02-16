from datetime import datetime
from typing import List

from kornetkover.stats.models.game import Game
from kornetkover.tools.scraper import Scraper

class GameService(object):

    def __init__(self, db):
        self.db = db

    def get_games_for_date(self, date: datetime.date) -> List[Game]:
        if date == datetime.now().date():
            return Scraper().scrape_upcoming_games()
        
        return self.get_games_from_db(date)
        
    def get_games_from_db(self, date: datetime.date) -> List[Game]:
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
