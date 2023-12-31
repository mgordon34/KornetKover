from datetime import datetime

from kornetkover.analysis.player_analysis import PlayerAnalysis
from kornetkover.players.player_service import PlayerService
from kornetkover.stats.pip_factor import PipFactor, RelationshipType
from kornetkover.stats.player_per import PlayerPer
from kornetkover.stats.player_stat import PlayerStat
from kornetkover.stats.player_stat_service import PlayerStatService
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

    def predict_stats(self, pip_factors: list[PipFactor], player_avgs: PlayerPer) -> PlayerStat:
        predicted_stats = {
            "minutes": 0,
            "points": 0,
            "rebounds": 0,
            "assists": 0,
        }
        count = 0
        for pip_factor in pip_factors:
            for stat in predicted_stats:
                yearly_stat = getattr(player_avgs, stat)
                stat_pchange = getattr(pip_factor, stat)
                if stat == "minutes":
                    predicted_stat = self.get_predicted_value(yearly_stat, stat_pchange)
                else:
                    predicted_stat = self.get_predicted_value(yearly_stat, stat_pchange) * player_avgs.minutes
                
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
