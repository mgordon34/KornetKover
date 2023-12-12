from datetime import datetime
from typing import List

from source.tools.db import DB
from source.stats.player_stat import PlayerStat
from source.stats.pip_factor import PipFactor


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
        sql = """SELECT COUNT(*), AVG(pg.minutes), AVG(pg.points), AVG(pg.assists), AVG(pg.rebounds), AVG(pg.ortg), AVG(pg.drtg) 
                 FROM player_games pg
                 LEFT join games gg ON gg.id=pg.game
                 WHERE pg.player_index='{0}' AND gg.date>'{1}' AND gg.date<'{2}'"""
        
        res = self.db.execute_query(sql.format(player_index, start_date, end_date))[0]
        stats = PlayerStat(frame, res[0], float(res[1]), float(res[2]), float(res[3]), float(res[4]), float(res[5]), float(res[6]))

        return stats

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
        sql = """SELECT COUNT(*), AVG(pg.minutes), AVG(pg.points), AVG(pg.assists), AVG(pg.rebounds), AVG(pg.ortg), AVG(pg.drtg)
                 FROM player_games pg
	             LEFT JOIN games gg ON gg.id = pg.game
	             WHERE pg.player_index='{0}' AND gg.date>'{2}' AND gg.date<'{3}'
                 AND (
                     SELECT COUNT(*) FROM games ga
                     LEFT JOIN player_games pg ON pg.game=ga.id
                     WHERE ga.id=gg.id AND pg.player_index IN ('{0}','{1}')
                 ) > 1;"""

        res = self.db.execute_query(sql.format(player_index, defender_index, start_date, end_date))[0]
        if not res[0]:
            return None

        player_stat = PlayerStat(frame, res[0], res[1], res[2], res[3], res[4], res[5], res[6])
        pip_factor = PipFactor(player_index, defender_index, player_stat)

        return pip_factor

    def get_pip(self, player_index, defender_index):
        sql = """SELECT frame, game_count, minutes, points, rebounds, assists, ortg, drtg from pip_factors
                 WHERE player_index='{0}' AND defender_index='{1}'"""

        res = self.db.execute_query(sql.format(player_index, defender_index))
        if not res:
            return None
        ps = PlayerStat(*res[0])
        return PipFactor(player_index, defender_index, ps)

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

    def calc_player_delta(self, player_avgs: PlayerStat, pip_factor: PipFactor) -> float:
        points_delta = pip_factor.player_stat.points - player_avgs.points 
        points_pchange = round((points_delta / player_avgs.points) * 100, 2)

        rebounds_delta = pip_factor.player_stat.rebounds - player_avgs.rebounds
        rebounds_pchange = round((rebounds_delta / player_avgs.rebounds) * 100, 2)

        assists_delta = pip_factor.player_stat.assists - player_avgs.assists
        assists_pchange = round((assists_delta / player_avgs.assists) * 100, 2)

        return {
            "points": points_pchange,
            "rebounds": rebounds_pchange,
            "assists": assists_pchange,
        }

    def analyze_player_matchups(self, team_one, team_two):
        for player in team_one:
            print(f"----------analyzing matchups for {player}----------")
            player_stats = self.calc_player_avgs(player, "2022-10-10", self.end_date, self.frame)
            for matchup in team_two:
                if matchup == player:
                    continue
                pip = self.get_pip(player, matchup)
                if not pip:
                    continue
                pchanges = self.calc_player_delta(player_stats, pip)
                for key, value in pchanges.items():
                    if value > 25 or value < -25:
                        print(f"[{pip.player_stat.num_games}]{player} matchup with {matchup} leads to {value} change in {key}. {round(getattr(player_stats, key), 2)}->{round(getattr(pip.player_stat, key), 2)}")




if __name__ == "__main__":
    start_date = "2017-10-01"
    end_date = "2023-12-03"
    player_index = "gordoaa01"
    defender_index = "bogdabo01"
    frame = 5

    db = DB()
    # db.initialize_tables()
    pss = PlayerStatService(db, start_date, end_date)
    pss.get_pip('murraja01', 'beysa01')

    team_one = ['jokicni01', 'murraja01', 'gordoaa01', 'portemi01']
    team_two = ['murrade01', 'capelca01', 'huntede01', 'youngtr01', 'beysa01', 'johnsja05']
    pss.analyze_player_matchups(team_one, team_two)
    pss.analyze_player_matchups(team_two, team_one)

    db.close()
