from datetime import datetime, timedelta

from kornetkover.analysis.services.analysis_service import AnalysisRunner
from kornetkover.analysis.prop_picker import PropPicker
from kornetkover.stats.models.player_stat import PlayerStat
from kornetkover.stats.services.player_service import PlayerService
from kornetkover.stats.services.player_stat_service import PlayerStatService
from kornetkover.odds.odds_service import OddsService
from kornetkover.odds.prop_line import PropLine
from kornetkover.tools.db import DB

class Backtester(object):
    def __init__(self, db: DB):
        self.db = db
        self.ar = AnalysisRunner(db)
        self.os = OddsService(db)
        self.ps = PlayerService(db)
        self.pss = PlayerStatService(db)
        self.pp = PropPicker(self.ps)

    def backtest_date(self, date: datetime.date) -> (int, int):
        print(f"backtesting for {date}")
        all_player_analyses = self.ar.run_analysis(date)

        best_props = self.pp.pick_props_historical(all_player_analyses, date)

        record = {
            "wins": 0,
            "losses": 0,
        }
        for best_stat_props in best_props:
            for (player, best_prop) in best_stat_props:
                side = "over" if best_prop.predicted_delta > 0 else "under"
                print(f"picking {side} {best_prop.line} {best_prop.stat} prop for {player.name}[{best_prop.predicted_delta}]")

                player_performance = self.pss.get_player_stat_for_date(player.index, date)
                stat_total = self.calculate_performance(player_performance, best_prop)

                if player_performance.minutes:
                    if best_prop.predicted_delta > 0:
                        if stat_total > best_prop.line:
                            record["wins"] += 1
                        else:
                            record["losses"] += 1
                    else:
                        if stat_total < best_prop.line:
                            record["wins"] += 1
                        else:
                            record["losses"] += 1

        print(f"{record['wins']} - {record['losses']}")
        return(record["wins"], record["losses"])

    def calculate_performance(self, player_performance: PlayerStat, prop_line: PropLine) -> int:
        stats = prop_line.stat.split("-")

        performance = 0
        for stat in stats:
            performance += getattr(player_performance, stat)

        return performance


if __name__ == "__main__":
    db = DB()
    bt = Backtester(db)

    date = datetime.strptime("2023-12-01", "%Y-%m-%d")
    # date = datetime.strptime("2024-01-01", "%Y-%m-%d")
    end_date = datetime.strptime("2023-12-31", "%Y-%m-%d")
    # end_date = datetime.strptime("2024-01-21", "%Y-%m-%d")

    wins = 0
    losses = 0
    while date <= end_date:
        (date_wins, date_losses) = bt.backtest_date(date)
        wins += date_wins
        losses += date_losses
        date = date + timedelta(days=1)

    print("=======Total========")
    print(f"WINS: {wins}, LOSSES: {losses}")
    print(f"Estimated Profit: {wins*9 - losses*10}")
