from typing import List

from datetime import datetime

from kornetkover.analysis.player_analysis import PlayerAnalysis
from kornetkover.odds.odds_service import OddsService
from kornetkover.odds.prop_line import PropLine
from kornetkover.stats.services.player_service import PlayerService
from kornetkover.stats.models.player import Player
from kornetkover.tools.db import DB

class PropPicker(object):
    props = []

    def __init__(self, player_service: PlayerService) -> None:
        self.ps = player_service
        self.stat_thresholds = {
            "points": 5,
            "rebounds": 1.5,
            "assists": 1.5,
        }
        return

    def pick_props(
        self,
        analyses: List[PlayerAnalysis],
        date: datetime.date,
    ) -> List[tuple[Player, List[PropLine]]]:
        db = DB()
        os = OddsService(db)

        best_props = []
        for analysis in analyses:
            player = self.ps.index_to_player(analysis.player_index)
            player_odds = os.get_player_odds(player.index, date)

            if not player_odds:
                continue

            prop_lines = player_odds.prop_lines
            for prop_line in prop_lines:
                stats = prop_line.stat.split("-")
                cumulative_stat = 0

                for stat in stats:
                    cumulative_stat += getattr(analysis.prediction, stat)

                prop_line.predicted_delta = cumulative_stat - prop_line.line

            prop_lines.sort(key=lambda item: abs(item.predicted_delta), reverse=True)
            best_props.append((player, prop_lines))

        best_props.sort(key=lambda item: item[1][0].predicted_delta, reverse=True)
        return best_props[:10] + best_props[-10:]

    def pick_props_historical(
        self,
        analyses: List[PlayerAnalysis],
        date: datetime.date,
    ) -> List[tuple[Player, List[PropLine]]]:
        db = DB()
        os = OddsService(db)

        best_props = {
            "points": [],
            "rebounds": [],
            "assists": [],
        }
        for analysis in analyses:
            player = self.ps.index_to_player(analysis.player_index)
            player_odds = os.get_specific_player_odds(player.index, self.stat_thresholds.keys(), date)

            if not player_odds:
                continue

            prop_lines = player_odds.prop_lines
            for prop_line in prop_lines:
                prop_line.predicted_delta = getattr(analysis.prediction, prop_line.stat) - prop_line.line

                if prop_line.predicted_delta < 0 and prop_line.under_odds < -140:
                    continue
                if prop_line.predicted_delta > 0 and prop_line.over_odds < -140:
                    continue

                if (abs(prop_line.predicted_delta) > self.stat_thresholds[prop_line.stat]
                        and prop_line.stat in analysis.outliers):
                    best_props[prop_line.stat].append((player, prop_line))

        for stat in best_props:
            best_props[stat].sort(key=lambda item: abs(item[1].predicted_delta), reverse=True)
        return [props[:6] for props in best_props.values()]
        return best_props
