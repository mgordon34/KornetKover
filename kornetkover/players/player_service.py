from datetime import datetime, timedelta

from kornetkover.tools.db import DB
from kornetkover.players.player import Player

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
            return None

        return res[0][0] + timedelta(days=1)


if __name__ == "__main__":
    db = DB()
    ps = PlayerService(db)
    db.initialize_tables()

    index = "whitede01"
    date = ps.find_date_on_active_team(index, 'BOS')
    print(date)
