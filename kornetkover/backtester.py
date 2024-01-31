from datetime import datetime, timedelta

from kornetkover.analysis.services.analysis_service import AnalysisRunner
from kornetkover.analysis.services.tracker import Tracker
from kornetkover.analysis.models.bet import Bet
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
        self.tracker = Tracker()

    def backtest_date(self, date: datetime.date) -> (int, int):
        print(f"backtesting for {date}")
        all_player_analyses = self.ar.run_analysis(date)

        best_props = self.pp.pick_props_historical(all_player_analyses, date)

        for best_stat_props in best_props:
            picked_players = []
            over_picks = 0
            under_picks = 0
            for (player, best_prop) in best_stat_props:
                side = "over" if best_prop.predicted_delta > 0 else "under"

                player_performance = self.pss.get_player_stat_for_date(player.index, date)

                stat_total = self.calculate_performance(player_performance, best_prop)
                print(f"picking {side} {best_prop.line} {best_prop.stat} prop for {player.name}[{best_prop.predicted_delta}] at {getattr(best_prop, side+'_odds')}. Actual: {stat_total}")

                if player_performance.minutes:
                    if best_prop.predicted_delta > 0:
                        if stat_total > best_prop.line:
                            result = "win"
                        else:
                            result = "loss"
                    else:
                        if stat_total < best_prop.line:
                            result = "win"
                        else:
                            result = "loss"
                result = "win"

                self.tracker.bets.append(Bet(player, best_prop, date, side, result))

                picked_players.append(player.index)
                if side == "over":
                    over_picks += 1
                if side == "under":
                    under_picks += 1

    def calculate_return(self, odds, bet_size):
        if odds < 0:
            return 100 / abs(odds) * bet_size
        else:
            return odds / 100 * bet_size


    def calculate_performance(self, player_performance: PlayerStat, prop_line: PropLine) -> int:
        stats = prop_line.stat.split("-")

        performance = 0
        for stat in stats:
            performance += getattr(player_performance, stat)

        return performance


if __name__ == "__main__":
    db = DB()
    bt = Backtester(db)

    # date = datetime.strptime("2023-11-01", "%Y-%m-%d").date()
    date = datetime.strptime("2024-01-01", "%Y-%m-%d").date()

    # end_date = datetime.strptime("2023-11-30", "%Y-%m-%d").date()
    end_date = datetime.strptime("2024-01-31", "%Y-%m-%d").date()

    while date <= end_date:
        bt.backtest_date(date)
        date = date + timedelta(days=1)

    bt.tracker.print_totals()
    for stat in ["points", "rebounds", "assists"]:
        bt.tracker.print_totals(bet_size=10, stat=stat)
        bt.tracker.analyze_totals(stat=stat)
