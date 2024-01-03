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


if __name__ == "__main__":
    db = DB()
    ps = PlayerService(db)
    db.initialize_tables()

    index = "jaime jaquez"
    player = ps.name_to_player(index)
    print(player.__dict__)
