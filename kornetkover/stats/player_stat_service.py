from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import List

from kornetkover.tools.db import DB
from kornetkover.stats.player_stat import PlayerStat
from kornetkover.stats.player_per import PlayerPer
from kornetkover.stats.pip_factor import PipFactor


class PlayerStatService(object):
    def __init__(self, db: DB, start_date="2017-10-01", end_date="2023-12-03") -> None:
        self.db = db
        self.start_date = start_date
        self.end_date = end_date
        self.frame = int(end_date.split("-")[0]) - int(start_date.split("-")[0])

    def calc_player_avgs(
        self,
        player_index: str,
        start_date: str,
        end_date: str,
        frame: int,
    ) -> PlayerStat:
        sql = """SELECT COUNT(*), AVG(pg.minutes), AVG(pg.points), AVG(pg.rebounds), AVG(pg.assists)
                 FROM player_games pg
                 LEFT join games gg ON gg.id=pg.game
                 WHERE pg.player_index='{0}' AND gg.date>'{1}' AND gg.date<'{2}'"""
        
        print(f"cur_date: {start_date}")
        print(f"end_date: {end_date}")
        res = self.db.execute_query(sql.format(player_index, start_date, end_date))[0]
        print(res)
        player_per = self.create_player_per(frame, *res)

        return player_per

    def calc_player_avgs_by_year(
        self,
        player_index: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        cur_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        player_avgs = {}


        while cur_date < end_date:
            cur_year = str(cur_date.year)
            next_date = cur_date + relativedelta(years=1)

            player_avgs[cur_year] = self.calc_player_avgs(player_index, cur_date.strftime("%Y-%m-%d"), next_date.strftime("%Y-%m-%d"), 1)
            cur_date = next_date

        return player_avgs

    def get_players(self, mins_floor: int) -> List[str]:
        sql = """SELECT pp.index FROM players pp
                 LEFT JOIN player_games pg ON pg.player_index = pp.index
                 GROUP BY pp.index HAVING AVG(pg.minutes)>{};"""
        
        res = self.db.execute_query(sql.format(mins_floor))
        return [player[0] for player in res]

    def calc_pip_factor(
        self,
        player_index: str,
        defender_index: str,
        start_date: str,
        end_date: str,
        frame: int,
    ) -> PipFactor:
        sql = """SELECT COUNT(*), AVG(pg.minutes), AVG(pg.points), AVG(pg.rebounds), AVG(pg.assists)
                 FROM player_games pg
	             LEFT JOIN games gg ON gg.id = pg.game
	             WHERE pg.player_index='{0}' AND gg.date>'{2}' AND gg.date<'{3}'
                 AND (
                     SELECT COUNT(*) FROM games ga
                     LEFT JOIN player_games pg ON pg.game=ga.id
                     WHERE ga.id=gg.id AND pg.player_index IN ('{0}','{1}')
                 ) > 1;"""

        res = self.db.execute_query(sql.format(player_index, defender_index, start_date, end_date))[0]
        if not res[0] or res[1] == 0:
            return None

        player_per = self.create_player_per(frame, *res)
        pip_factor = PipFactor(player_index, defender_index, player_per)

        return pip_factor

    def create_player_per(
        self,
        frame: int,
        num_games: int,
        avg_minutes: Decimal,
        avg_points: Decimal,
        avg_rebounds: Decimal,
        avg_assists: Decimal,
    ) -> PlayerPer:
        avg_minutes = float(avg_minutes)
        points_per = float(avg_points) / avg_minutes
        rebounds_per = float(avg_rebounds) / avg_minutes
        assists_per = float(avg_assists) / avg_minutes

        return PlayerPer(frame, num_games, avg_minutes, points_per, rebounds_per, assists_per)


    def calc_missing_teammate_pip_factor(
        self,
        player_index: str,
        teammate_index: str,
    ) -> PipFactor:
        start_date = "2023-10-10"
        end_date = datetime.now().strftime("%Y-%m-%d")
        frame = 0
        sql = """SELECT COUNT(*), AVG(pg.minutes), AVG(pg.points), AVG(pg.rebounds), AVG(pg.assists)
                 FROM player_games pg
	             LEFT JOIN games gg ON gg.id = pg.game
	             WHERE pg.player_index='{0}' AND gg.date>'{2}' AND gg.date<'{3}'
                 AND (
                     SELECT COUNT(*) FROM games ga
                     LEFT JOIN player_games pg ON pg.game=ga.id
                     WHERE ga.id=gg.id AND pg.player_index='{0}'
                 ) = 1
                 AND (
                     SELECT COUNT(*) FROM games ga
                     LEFT JOIN player_games pg ON pg.game=ga.id
                     WHERE ga.id=gg.id AND pg.player_index='{1}'
                 ) = 0;"""

        res = self.db.execute_query(sql.format(player_index, teammate_index, start_date, end_date))[0]
        if not res[0]:
            return None

        player_per = self.create_player_per(frame, *res)
        pip_factor = PipFactor(player_index, teammate_index, player_per)

        return pip_factor

    def get_pip(self, player_index, defender_index):
        sql = """SELECT frame, game_count, minutes, points, rebounds, assists from pip_factors
                 WHERE player_index='{0}' AND defender_index='{1}'"""

        res = self.db.execute_query(sql.format(player_index, defender_index))
        if not res:
            return None
        player_per = PlayerPer(*res[0])
        return PipFactor(player_index, defender_index, player_per)

    def calc_all_players_pip_factor(
        self,
        min_floor: int,
        start_date: str,
        end_date: str,
        frame: int,
    ) -> None:
        players = self.get_players(min_floor)

        for player in players:
            pip_factors = []
            for defender in players:
                if player == defender:
                    continue

                pip_factor = self.calc_pip_factor(player, defender, start_date, end_date, frame)
                if pip_factor:
                    pip_factors.append(pip_factor.to_db())

            count = self.db.add_pip_factors(pip_factors)
            print(f"{count} pip_factors added for player {player}")


if __name__ == "__main__":
    start_date = "2017-10-01"
    end_date = "2023-12-03"
    player_index = "gordoaa01"
    defender_index = "bogdabo01"
    frame = 5

    db = DB()
    db.initialize_tables()

    pss = PlayerStatService(db, start_date, end_date)
    # pss.calc_all_players_pip_factor(10, start_date, end_date, frame)
    stats = pss.calc_player_avgs_by_year('tatumja01', '2018-10-10', '2023-12-19')
    for year in stats:
        player_per = stats[year]
        print(f"{year} season: {player_per.points * player_per.minutes} PTS")

    db.close()
