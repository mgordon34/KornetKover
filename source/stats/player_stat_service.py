from datetime import datetime

from source.db import DB
from source.stats.player_stat import PlayerStat


class PlayerStatService(object):
    def __init__(self, db: DB) -> None:
        self.db = db

    def calc_player_avgs(
        self,
        player_index: str,
        start_date: str,
        end_date: str,
        frame: int,
    ) -> dict:
        sql = """SELECT COUNT(*), AVG(pg.minutes), AVG(pg.points), AVG(pg.assists), AVG(pg.rebounds) FROM player_games pg
                 LEFT join games gg ON gg.id=pg.game
                 WHERE pg.player_index='{0}' AND gg.date>'{1}' AND gg.date<'{2}'"""
        
        res = self.db.execute_query(sql.format(player_index, start_date, end_date))
        stats = PlayerStat(frame, res[0], float(res[1]), float(res[2]), float(res[3]), float(res[4]))

        return stats


if __name__ == "__main__":
    db = DB()
    pss = PlayerStatService(db)

    start_date = "2022-10-10"
    end_date = "2023-04-10"
    player_index = "tatumja01"
    frame = 1
    pss.calc_player_avgs(player_index, start_date, end_date, frame)

    db.close()