from datetime import datetime
from typing import List, Optional

from kornetkover.analysis.player_analysis import PlayerAnalysis
from kornetkover.stats.services.player_service import PlayerService
from kornetkover.stats.models.game import Game
from kornetkover.stats.models.player import Player
from kornetkover.stats.models.pip_factor import PipFactor, RelationshipType
from kornetkover.stats.models.player_per import PlayerPer
from kornetkover.stats.models.player_stat import PlayerStat
from kornetkover.stats.services.player_stat_service import PlayerStatService
from kornetkover.stats.utils import get_nba_year_from_date, str_to_date
from kornetkover.tools.db import DB

class MatchupAnalysisService(object):
    def __init__(
            self, db: DB,
            start_date="2018-10-01",
            end_date=datetime.now().strftime("%Y-%m-%d"),
    ) -> None:
        self.db = db 
        self.start_date = start_date
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        self.end_date = end_date
        self.frame = int(end_date.split("-")[0]) - int(start_date.split("-")[0])

        self.pss = PlayerStatService(db)

    def analyze_player_matchups(self, team_one, team_two, p_threshold=25, date=datetime.now().date()):
        ps = PlayerService(self.db)
        team_name = team_one["team_name"]
        player_analyses = []
        
        for player in team_one["starting"]:
            player_stats = self.pss.calc_player_avgs_by_year(player, str_to_date(self.start_date), str_to_date(self.end_date))
            current_stats = player_stats[get_nba_year_from_date(str_to_date(self.end_date))]
            date_on_team = ps.find_date_on_active_team(player, team_name)

            if not current_stats:
                continue

            player_analysis = PlayerAnalysis(player, date, current_stats)
            print("----------analyzing matchups for {}: MIN[{}], PTS[{}], REB[{}], AST[{}]----------".format(
                player,
                round(current_stats.minutes, 2),
                round(current_stats.points * current_stats.minutes, 2),
                round(current_stats.rebounds * current_stats.minutes, 2),
                round(current_stats.assists * current_stats.minutes, 2),
            ))

            for teammate in team_one["out"]:
                teammate_on_team = ps.find_date_on_active_team(teammate, team_name)
                related_games = self.pss.get_related_games(player, teammate, RelationshipType.TEAMMATE, max(date_on_team, teammate_on_team), self.end_date)
                pip_factor = self.pss.calc_pip_factor(player, teammate, RelationshipType.TEAMMATE, player_stats, related_games)
                if not pip_factor:
                    continue
                player_analysis.add_pip_factor(pip_factor)

                notable_stats = self.find_notable_stats(pip_factor, p_threshold)
                for stat in notable_stats:
                    stat_pchange = round(getattr(pip_factor, stat), 2)
                    current_stat_value = getattr(current_stats, stat)
                    if stat != "minutes":
                        current_stat_value = current_stat_value * current_stats.minutes

                    predicted_stat = self.get_predicted_value(current_stat_value, stat_pchange)
                    print(f"[{pip_factor.num_games}]{player} with {teammate} missing leads to {stat_pchange} change in {stat}: {predicted_stat}")
            for matchup in team_two["starting"]:
                related_games = self.pss.get_related_games(player, matchup, RelationshipType.OPPONENT, self.start_date, self.end_date)
                pip_factor = self.pss.calc_pip_factor(player, matchup, RelationshipType.OPPONENT, player_stats, related_games)
                if not pip_factor:
                    continue
                player_analysis.add_pip_factor(pip_factor)

                notable_stats = self.find_notable_stats(pip_factor, p_threshold)
                for stat in notable_stats:
                    stat_pchange = round(getattr(pip_factor, stat), 2)
                    current_stat_value = getattr(current_stats, stat)
                    if stat != "minutes":
                        current_stat_value = current_stat_value * current_stats.minutes

                    predicted_stat = self.get_predicted_value(current_stat_value, stat_pchange)
                    print(f"[{pip_factor.num_games}]{player} matchup with {matchup} leads to {stat_pchange} change in {stat}: {predicted_stat}")

            player_analysis.prediction = self.predict_stats(player_analysis.pip_factors, current_stats)
            outliers = self.find_outlying_stats(player_analysis.prediction, current_stats)
            if outliers and len(player_analysis.pip_factors) > 5:
                [print(f"Notable Outlier {outlier}: {outliers[outlier]}") for outlier in outliers]
            print("Predicted stats: MIN[{}], PTS[{}], REB[{}], AST[{}]".format(
                player_analysis.prediction.minutes,
                player_analysis.prediction.points,
                player_analysis.prediction.rebounds,
                player_analysis.prediction.assists,
            ))

            player_analyses.append(player_analysis)

        return player_analyses

    def get_player_analyses_per_team(
        self,
        game: Game,
        team_index: str,
        players: List[Player],
        defenders: List[Player],
    ) -> List[PlayerAnalysis]:
        all_player_analyses = []

        for player in players:
            yearly_base_stats = self.pss.calc_player_avgs_by_year(player.index, str_to_date(self.start_date), game.date)
            current_stats = yearly_base_stats[get_nba_year_from_date(game.date)]
            stats_with_roster = self.pss.calc_stats_with_roster(player, team_index, players, game)

            base_stats = self.pick_base_stats(stats_with_roster, current_stats)
            if not base_stats:
                print(f"skipping analysis for {player.name}, no base stats")
                continue

            all_player_analyses.append(self.run_pip_analysis(player, base_stats, yearly_base_stats, defenders, game.date))

        return all_player_analyses

    def pick_base_stats(self, roster_stats: PlayerPer, yearly_stats: PlayerPer) -> Optional[PlayerPer]:
        if roster_stats and roster_stats.num_games > 2:
            return roster_stats

        if yearly_stats.num_games > 4:
            print("Using yearly stats")
            return yearly_stats

        return None

    def run_pip_analysis(
        self,
        player: Player,
        base_stats: PlayerPer,
        all_stats: dict[PlayerPer],
        defenders,
        date: datetime.date,
    ) -> PlayerAnalysis:
        player_analysis = PlayerAnalysis(player.index, date, base_stats)

        for matchup in defenders:
            related_games = self.pss.get_related_games(player.index, matchup.index, RelationshipType.OPPONENT, self.start_date, date)
            pip_factor = self.pss.calc_pip_factor(player.index, matchup.index, RelationshipType.OPPONENT, all_stats, related_games)

            if not pip_factor:
                continue

            player_analysis.add_pip_factor(pip_factor)

        player_analysis.prediction = self.predict_stats(player_analysis.pip_factors, base_stats)

        return player_analysis


    def find_notable_stats(self, pip_factor: PipFactor, p_threshold: int):
        stats = ["minutes", "points", "rebounds", "assists"]

        notable_stats = []
        for stat in stats:
            pip_stat = getattr(pip_factor, stat)
            if pip_stat > p_threshold or pip_stat < -p_threshold:
                notable_stats.append(stat)

        return notable_stats

    def get_predicted_value(self, current_value: float, pchange: float) -> float:
        predicted_value = current_value + (current_value * pchange/100)
        return round(predicted_value, 2)

    def predict_stats(self, pip_factors: list[PipFactor], base_stats: PlayerPer) -> PlayerStat:
        predicted_stats = {
            "minutes": 0,
            "points": 0,
            "rebounds": 0,
            "assists": 0,
        }
        count = 0
        for pip_factor in pip_factors:
            for stat in predicted_stats:
                base_stat = getattr(base_stats, stat)
                stat_pchange = getattr(pip_factor, stat)
                if stat == "minutes":
                    predicted_stat = self.get_predicted_value(base_stat, stat_pchange)
                else:
                    predicted_stat = self.get_predicted_value(base_stat, stat_pchange) * base_stats.minutes
                
                predicted_stats[stat] = (predicted_stats[stat] * count + predicted_stat * pip_factor.num_games) / float(count + pip_factor.num_games)
            count = count + pip_factor.num_games
        
        return PlayerStat(
            round(predicted_stats["minutes"], 2),
            round(predicted_stats["points"], 2),
            round(predicted_stats["rebounds"], 2),
            round(predicted_stats["assists"], 2),
        )
    
    def find_outlying_stats(self, predicted_stats: PlayerStat, yearly_stats: PlayerPer):
        stats = ["minutes", "points", "rebounds", "assists"]
        outliers = {}
        for stat in stats:
            predicted_stat = getattr(predicted_stats, stat)
            yearly_avg_stat = getattr(yearly_stats, stat) * yearly_stats.minutes if stat != "minutes" else getattr(yearly_stats, stat)

            stat_diff = predicted_stat - yearly_avg_stat
            stat_pchange = (stat_diff / yearly_avg_stat) * 100
            if abs(stat_diff) > 1 and abs(stat_pchange) > 10:
                outliers[stat] = predicted_stat
        
        return outliers
