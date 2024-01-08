from datetime import datetime

from kornetkover.analysis.matchup_analysis_service import MatchupAnalysisService
from kornetkover.analysis.prop_picker import PropPicker
from kornetkover.tools.db import DB
from kornetkover.odds.odds_service import OddsService
from kornetkover.players.player_service import PlayerService
from kornetkover.tools.scraper import Scraper

db = DB()
db.initialize_tables()
mas = MatchupAnalysisService(db)
ps = PlayerService(db)
os = OddsService(db)
date = datetime.now().date()

rosters = Scraper.get_rosters_for_upcoming_games()

all_game_analyses = []
for game, roster in rosters.items():
    analyses = []

    print(f"----------Analyzing matchups for {game}----------")
    analyses += mas.analyze_player_matchups(roster["away"], roster["home"])
    analyses += mas.analyze_player_matchups(roster["home"], roster["away"])
    print("-------------------------------------------------\n")

    for analysis in analyses:
        player = ps.index_to_player(analysis.player_index)
        player_odds = os.get_player_odds(player.index, date)

        if not player_odds:
            continue

        used_stats = ["points", "rebounds", "assists"]
        display_str = f"[{player.name:<20}]: "
        for stat in used_stats:
            for prop_line in player_odds.prop_lines:
                if prop_line.stat != stat:
                    continue

                stat_diff = round(getattr(analysis.prediction, stat) - prop_line.line, 2)
                display_str += f"{stat}: {stat_diff:<8}"

        print(display_str)

    print("-------------------------------------------------\n")
    all_game_analyses += analyses

pp = PropPicker(ps)
best_props = pp.pick_props(all_game_analyses, date)

for player, prop_lines in best_props:
    display_str = f"{player.name:<20}"
    for prop_line in prop_lines:
        display_str += f"{prop_line.stat:<15}: {round(prop_line.predicted_delta, 2):<8}"

    print(display_str)

