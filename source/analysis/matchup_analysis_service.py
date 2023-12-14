from datetime import datetime

from source.stats.pip_factor import PipFactor
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
        for player in team_one["starting"]:
            print(f"----------analyzing matchups for {player}----------")
            player_stats = self.pss.calc_player_avgs(player, "2022-10-10", self.end_date, self.frame)
            for teammate in team_one["out"]:
                pip = self.pss.calc_missing_teammate_pip_factor(player, teammate)
                if not pip:
                    continue
                pchanges = self.calc_player_delta(player_stats, pip)
                minutes_delta = pip.player_stat.minutes - player_stats.minutes
                pchanges["minutes"] = round((minutes_delta / player_stats.minutes) * 100, 2)
                for key, value in pchanges.items():
                    if value > 25 or value < -25:
                        print(f"[{pip.player_stat.num_games}]{player} with {teammate} missing leads to {value} change in {key}. {round(getattr(player_stats, key), 2)}->{round(getattr(pip.player_stat, key), 2)}")
            for matchup in team_two["starting"]:
                pip = self.pss.get_pip(player, matchup)
                if not pip:
                    continue
                pchanges = self.calc_player_delta(player_stats, pip)
                for key, value in pchanges.items():
                    if value > 25 or value < -25:
                        print(f"[{pip.player_stat.num_games}]{player} matchup with {matchup} leads to {value} change in {key}. {round(getattr(player_stats, key), 2)}->{round(getattr(pip.player_stat, key), 2)}")
