from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import List

from kornetkover.tools.db import DB
from kornetkover.stats.models.game import Game
from kornetkover.stats.models.player import Player
from kornetkover.stats.models.player_stat import PlayerStat
from kornetkover.stats.models.player_per import PlayerPer
from kornetkover.stats.models.pip_factor import PipFactor, RelationshipType
from kornetkover.stats.utils import get_nba_year_from_date


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
        
        res = self.db.execute_query(sql.format(player_index, start_date, end_date))[0]
        if not res or not res[0]:
            return None
        player_per = self.create_player_per(frame, *res)

        return player_per

    def calc_player_avgs_by_year(
        self,
        player_index: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> dict:
        cur_date = start_date
        player_avgs = {}

        while cur_date < end_date:
            cur_year = str(cur_date.year)
            next_date = min(cur_date + relativedelta(years=1), end_date)

            player_avgs[cur_year] = self.calc_player_avgs(player_index, cur_date.strftime("%Y-%m-%d"), next_date.strftime("%Y-%m-%d"), 1)
            cur_date = next_date

        return player_avgs

    def get_players(self, mins_floor: int) -> List[str]:
        sql = """SELECT pp.index FROM players pp
                 LEFT JOIN player_games pg ON pg.player_index = pp.index
                 GROUP BY pp.index HAVING AVG(pg.minutes)>{};"""
        
        res = self.db.execute_query(sql.format(mins_floor))
        return [player[0] for player in res]

    def get_related_games(
        self,
        primary_index: str,
        other_index: str,
        relationship: RelationshipType,
        start_date: str,
        end_date: str,
    ) -> List[PlayerPer]:
        base_sql = """SELECT pg.minutes, pg.points, pg.rebounds, pg.assists, gg.date
                      FROM player_games pg
                      LEFT JOIN games gg ON gg.id = pg.game
                      WHERE pg.player_index='{0}' AND gg.date>'{2}' AND gg.date<'{3}'"""
        opponent_filter = """
                AND (
                    SELECT COUNT(*) FROM games ga
                    LEFT JOIN player_games pg ON pg.game=ga.id
                    WHERE ga.id=gg.id AND pg.player_index IN ('{0}','{1}')
                ) > 1;"""
        teammate_filter = """
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

        if relationship == RelationshipType.TEAMMATE:
            sql = base_sql + teammate_filter
        else:
            sql = base_sql + opponent_filter

        player_stats = []
        res = self.db.execute_query(sql.format(primary_index, other_index, start_date, end_date))
        for game in res:
            player_stats.append((PlayerStat(*game)))

        return player_stats

    def get_games_for_date(self, date: datetime.date) -> List[Game]:
        sql = f"""SELECT id, home_index, away_index, date, home_score, away_score
                  FROM games
                  WHERE date=Date('{date}')"""

        res = self.db.execute_query(sql)

        games = []
        for game in res:
            games.append(Game(*game))

        return games

    def get_player_stats_for_game(self, game: Game) -> dict:
        sql = f"""SELECT pg.player_index, pl.name, pg.team_index, pg.minutes, pg.points, pg.rebounds, pg.assists
                 FROM player_games pg
                 LEFT JOIN games ga ON ga.id=pg.game
                 LEFT JOIN players pl ON pl.index=pg.player_index
                 WHERE ga.id={game.id}"""

        res = self.db.execute_query(sql)

        roster = defaultdict(list)
        for player_stat in res:
            player = Player(player_stat[0], player_stat[1])
            roster[player_stat[2]].append((player, PlayerStat(*player_stat[3:])))

        return roster

    def calc_pip_factor(
        self,
        primary_index: str,
        other_index: str,
        relationship: RelationshipType,
        player_pers: dict,
        related_games: list[PlayerStat],
    ) -> PipFactor:
        total_pchanges = {
            "minutes": 0.0,
            "points": 0.0,
            "rebounds": 0.0,
            "assists": 0.0,
        }
        game_count = 0
        for game in related_games:
            if game.minutes == 0:
                continue

            yearly_per = player_pers[get_nba_year_from_date(game.date)]
            game_per = self.create_player_per(1, 1, game.minutes, game.points, game.rebounds, game.assists)
            pchanges = self.calc_player_delta(yearly_per, game_per)

            for stat in total_pchanges:
                total_pchanges[stat] = total_pchanges[stat] + pchanges[stat]
            game_count += 1

        if game_count == 0:
            return None
        return PipFactor(primary_index, other_index, relationship, game_count, total_pchanges["minutes"]/game_count, total_pchanges["points"]/game_count, total_pchanges["rebounds"]/game_count, total_pchanges["assists"]/game_count)


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

    def calc_player_delta(self, player_avgs: PlayerPer, game: PlayerPer) -> float:
        points_delta = game.points - player_avgs.points
        points_pchange = round((points_delta / player_avgs.points) * 100, 2) if player_avgs.points else 0

        rebounds_delta = game.rebounds - player_avgs.rebounds
        rebounds_pchange = round((rebounds_delta / player_avgs.rebounds) * 100, 2) if player_avgs.rebounds else 0

        assists_delta = game.assists - player_avgs.assists
        assists_pchange = round((assists_delta / player_avgs.assists) * 100, 2) if player_avgs.assists else 0

        minutes_delta = game.minutes - player_avgs.minutes
        minutes_pchange = round((minutes_delta / player_avgs.minutes) * 100, 2) if player_avgs.minutes else 0

        return {
            "points": points_pchange,
            "rebounds": rebounds_pchange,
            "assists": assists_pchange,
            "minutes": minutes_pchange,
        }


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

    def calc_stats_with_roster(
        self,
        player: Player,
        team_index: str,
        players: List[Player],
        game: Game,
    ) -> PlayerPer:
        roster_string = ",".join([f"'{p.index}'" for p in players])
        sql = f"""SELECT COUNT(*), AVG(pg.minutes), AVG(pg.points), AVG(pg.rebounds), AVG(pg.assists)
                      FROM player_games pg
                      LEFT JOIN games gg ON gg.id = pg.game
                      WHERE pg.player_index='{player.index}' AND gg.date<'{game.date}'
                      AND (
                          SELECT COUNT(*) FROM games ga
                          LEFT JOIN player_games pg ON pg.game=ga.id
                          WHERE ga.id=gg.id AND pg.player_index IN ({roster_string}) AND pg.team_index='{team_index}'
                      ) = {len(players)};"""

        res = self.db.execute_query(sql)
        if not res or not res[0]:
            return None

        return self.create_player_per(1, *res[0])


if __name__ == "__main__":
    start_date = "2018-10-01"
    end_date = "2024-01-10"
    player_index = "jamesle01"
    defender_index = "embiijo01"
    frame = 5

    db = DB()
    db.initialize_tables()

    pss = PlayerStatService(db, start_date, end_date)
    date = datetime.strptime(end_date, "%Y-%m-%d").date()
    games = pss.get_games_for_date(date)

    for game in games:
        roster = pss.get_player_stats_for_game(game)
        for team, players in roster.items():
            print(f"player_stats for {team}--------------")
            for (player, stats) in players:
                print(f"{player.name} has {stats.minutes} mins, {stats.points} points, {stats.rebounds} rebounds, {stats.assists} assists")
        print("\n")

    db.close()
