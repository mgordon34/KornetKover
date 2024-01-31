from datetime import datetime

from kornetkover.analysis.matchup_analysis_service import MatchupAnalysisService
from kornetkover.analysis.prop_picker import PropPicker
from kornetkover.analysis.services.analysis_service import AnalysisRunner
from kornetkover.tools.db import DB
from kornetkover.odds.odds_service import OddsService
from kornetkover.stats.services.player_service import PlayerService
from kornetkover.tools.scraper import Scraper

db = DB()
db.initialize_tables()
mas = MatchupAnalysisService(db)
ps = PlayerService(db)
os = OddsService(db)
ar = AnalysisRunner(db)
pp = PropPicker(ps)
date = datetime.now().date()

all_player_analyses = ar.run_analysis(date)

best_props = pp.pick_props_historical(all_player_analyses, date)

for best_stat_props in best_props:
    picked_players = []
    over_picks = 0
    under_picks = 0
    for (player, best_prop) in best_stat_props:
        side = "over" if best_prop.predicted_delta > 0 else "under"

        print(f"picking {side} {best_prop.line} {best_prop.stat} prop for {player.name}[{best_prop.predicted_delta}] at {getattr(best_prop, side+'_odds')}")

        picked_players.append(player.index)
