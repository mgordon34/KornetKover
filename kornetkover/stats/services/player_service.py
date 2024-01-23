from datetime import datetime, timedelta
from typing import List
from unidecode import unidecode

from kornetkover.tools.db import DB
from kornetkover.stats.models.player import Player
from kornetkover.stats.models.game import Game

class PlayerService(object):
    def __init__(self, db: DB):
        self.db = db

    def index_to_player(self, index: str):
        sql = """SELECT index, name from players
                  WHERE index='{}'"""

        res = self.db.execute_query(sql.format(index))
        if not res or not res[0]:
            return None

        player = res[0]
        return Player(player[0], player[1])

    def name_to_player(self, name: str):
        sql = """SELECT index, name from players
                  WHERE UPPER(name) LIKE UPPER('%{}%')"""

        res = self.db.execute_query(sql.format(name))
        if not res or not res[0]:
            return None

        player = res[0]
        return Player(player[0], player[1])


    def find_date_on_active_team(self, player_index: str, team: str) -> datetime.date:
        sql = """SELECT gg.date
                 FROM player_games pg
                 LEFT join games gg ON gg.id=pg.game
                 WHERE pg.player_index='{0}' AND pg.team_index!='{1}'
                 ORDER BY gg.date DESC"""

        res = self.db.execute_query(sql.format(player_index, team))
        if not res or not res[0]:
            return datetime.strptime("2017-10-10", "%Y-%m-%d").date()

        return res[0][0] + timedelta(days=1)

    def find_roster_for_game(self, game_id, team: str) -> List[Player]:
        sql = f"""SELECT pl.index, pl.name, pg.team_index FROM players pl
                 LEFT JOIN player_games pg ON pg.player_index=pl.index
                 LEFT JOIN games gg ON gg.id=pg.game
                 WHERE gg.id={game_id} AND pg.team_index='{team}'
                 ORDER BY pg.minutes DESC
                 LIMIT 8"""

        res = self.db.execute_query(sql)
        if not res or not res[0]:
            return None

        return [ Player(*player) for player in res ] 

    @classmethod
    def normalize_player_name(cls, name: str) -> str:
        return " ".join(unidecode(name).replace("'", " ").replace("-", " ").split(" ")[:2]).lower()


if __name__ == "__main__":
    db = DB()
    ps = PlayerService(db)
    db.initialize_tables()

    index = "willipa01"
    date = ps.find_date_on_active_team(index, 'CHI')
    print(date)
