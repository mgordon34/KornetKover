from datetime import datetime

from source.analysis.player_analysis import PlayerAnalysis
from source.stats.pip_factor import PipFactor
from source.stats.player_per import PlayerPer
from source.stats.player_stat import PlayerStat
from source.stats.player_stat_service import PlayerStatService
from source.tools.db import DB

class MatchupAnalysisService(object):
    def __init__(
            self, db: DB,
            start_date="2017-10-01",
            end_date=datetime.now().strftime("%Y-%m-%d"),
    ) -> None:
        self.db = db 
        self.start_date = start_date
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        self.end_date = end_date
        self.frame = int(end_date.split("-")[0]) - int(start_date.split("-")[0])

        self.pss = PlayerStatService(db)

    def calc_player_delta(self, player_avgs: PlayerPer, pip_factor: PipFactor) -> float:
        points_delta = pip_factor.player_per.points - player_avgs.points
        points_pchange = round((points_delta / player_avgs.points) * 100, 2)

        rebounds_delta = pip_factor.player_per.rebounds - player_avgs.rebounds
        rebounds_pchange = round((rebounds_delta / player_avgs.rebounds) * 100, 2)

        assists_delta = pip_factor.player_per.assists - player_avgs.assists
        assists_pchange = round((assists_delta / player_avgs.assists) * 100, 2)

        minutes_delta = pip_factor.player_per.minutes - player_avgs.minutes
        minutes_pchange = round((minutes_delta / player_avgs.minutes) * 100, 2)

        return {
            "points": points_pchange,
            "rebounds": rebounds_pchange,
            "assists": assists_pchange,
            "minutes": minutes_pchange,
        }

    def analyze_player_matchups(self, team_one, team_two, p_threshold=25, date=datetime.now().date()):
        for player in team_one["starting"]:
            player_analysis = PlayerAnalysis(player, date)
            player_stats = self.pss.calc_player_avgs(player, "2022-10-10", self.end_date, self.frame)
            print("----------analyzing matchups for {}: MIN[{}], PTS[{}], REB[{}], AST[{}]----------".format(
                player,
                round(player_stats.minutes, 2),
                round(player_stats.points * player_stats.minutes, 2),
                round(player_stats.rebounds * player_stats.minutes, 2),
                round(player_stats.assists * player_stats.minutes, 2),
            ))
            for teammate in team_one["out"]:
                pip = self.pss.calc_missing_teammate_pip_factor(player, teammate)
                if not pip:
                    continue
                pchanges = self.calc_player_delta(player_stats, pip)
                for key, value in pchanges.items():
                    if value > p_threshold or value < -p_threshold:
                        predicted_stat = getattr(pip.player_per, key)
                        if key != "minutes":
                            predicted_stat = predicted_stat * pip.player_per.minutes
                        predicted_stat = round(predicted_stat, 2)
                        print(f"[{pip.player_per.num_games}]{player} with {teammate} missing leads to {value} change in {key}. {predicted_stat} on {round(pip.player_per.minutes,2)} minutes")
            for matchup in team_two["starting"]:
                pip = self.pss.get_pip(player, matchup)
                if not pip:
                    continue
                pchanges = self.calc_player_delta(player_stats, pip)
                for key, value in pchanges.items():
                    if value > p_threshold or value < -p_threshold:
                        predicted_stat = getattr(pip.player_per, key)
                        if key != "minutes":
                            predicted_stat = predicted_stat * pip.player_per.minutes
                        predicted_stat = round(predicted_stat, 2)
                        print(f"[{pip.player_per.num_games}]{player} matchup with {matchup} leads to {value} change in {key}. {predicted_stat} on {round(pip.player_per.minutes,2)} minutes")
