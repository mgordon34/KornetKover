from typing import List

from datetime import datetime

from kornetkover.analysis.player_analysis import PlayerAnalysis
from kornetkover.odds.odds_service import OddsService
from kornetkover.odds.prop_line import PropLine
from kornetkover.players.player_service import PlayerService
from kornetkover.players.player import Player
from kornetkover.tools.db import DB


class PropPicker(object):
    props = []

    def __init__(self, player_service: PlayerService) -> None:
        self.ps = player_service
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

        best_props.sort(key=lambda item: item[1][1].predicted_delta, reverse=True)
        return best_props[:6] + best_props[-6:]
