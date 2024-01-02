from kornetkover.tools.db import DB
from kornetkover.players.player import Player

class PlayerService(object):
    def __init__(self, db: DB):
        self.db = db

    def index_to_name(self, index: str):
        sql = """SELECT index, name from players
                  WHERE index='{}'"""

        res = self.db.execute_query(sql.format(index))[0]
        if not res or not res[0]:
            return None

        return Player(res[0], res[1])

if __name__ == "__main__":
    db = DB()
    ps = PlayerService(db)
    db.initialize_tables()

    index = "tatumja01"
    player = ps.index_to_name(index)
    print(player.__dict__)
