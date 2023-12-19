from datetime import datetime

from kornetkover.analysis.player_analysis import PlayerAnalysis
from kornetkover.stats.pip_factor import PipFactor
from kornetkover.stats.player_per import PlayerPer
from kornetkover.stats.player_stat import PlayerStat
from kornetkover.stats.player_stat_service import PlayerStatService
from kornetkover.stats.utils import date_to_str, get_nba_year_from_date, str_to_date
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
        for player in team_one["starting"]:
            player_analysis = PlayerAnalysis(player, date)
            player_stats = self.pss.calc_player_avgs_by_year(player, str_to_date(self.start_date), str_to_date(self.end_date))
            current_stats = player_stats[get_nba_year_from_date(str_to_date(self.end_date))]
            print("----------analyzing matchups for {}: MIN[{}], PTS[{}], REB[{}], AST[{}]----------".format(
                player,
                round(current_stats.minutes, 2),
                round(current_stats.points * current_stats.minutes, 2),
                round(current_stats.rebounds * current_stats.minutes, 2),
                round(current_stats.assists * current_stats.minutes, 2),
            ))

            for teammate in team_one["out"]:
                related_games = self.pss.get_related_games(player, teammate, True, "2023-10-10", self.end_date)
                pip_factor = self.pss.calc_pip_factor(player, teammate, player_stats, related_games)
                if not pip_factor:
                    continue

                notable_stats = self.find_notable_stats(pip_factor, p_threshold)
                for stat in notable_stats:
                    stat_pchange = round(getattr(pip_factor, stat), 2)
                    current_stat_value = getattr(current_stats, stat)
                    if stat != "minutes":
                        current_stat_value = current_stat_value * current_stats.minutes

                    predicted_stat = self.get_predicted_value(current_stat_value, stat_pchange)
                    print(f"[{pip_factor.num_games}]{player} with {teammate} missing leads to {stat_pchange} change in {stat}: {predicted_stat}")
            for matchup in team_two["starting"]:
                related_games = self.pss.get_related_games(player, matchup, False, self.start_date, self.end_date)
                pip_factor = self.pss.calc_pip_factor(player, matchup, player_stats, related_games)
                if not pip_factor:
                    continue

                notable_stats = self.find_notable_stats(pip_factor, p_threshold)
                for stat in notable_stats:
                    stat_pchange = round(getattr(pip_factor, stat), 2)
                    current_stat_value = getattr(current_stats, stat)
                    if stat != "minutes":
                        current_stat_value = current_stat_value * current_stats.minutes

                    predicted_stat = self.get_predicted_value(current_stat_value, stat_pchange)
                    print(f"[{pip_factor.num_games}]{player} matchup with {matchup} leads to {stat_pchange} change in {stat}: {predicted_stat}")

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
