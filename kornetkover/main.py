from datetime import datetime
from unidecode import unidecode

from kornetkover.analysis.matchup_analysis_service import MatchupAnalysisService
from kornetkover.tools.db import DB
from kornetkover.players.player_service import PlayerService
from kornetkover.players.player import Player
from kornetkover.stats.player_stat_service import PlayerStatService
from kornetkover.tools.scraper import Scraper
from kornetkover.odds.player_odds import PlayerOdds

db = DB()
db.initialize_tables()
mas = MatchupAnalysisService(db)
ps = PlayerService(db)
date = datetime.now().date()

rosters = Scraper.get_rosters_for_upcoming_games()
for roster in rosters:
    print(rosters[roster])

prop_lines = Scraper.get_prop_lines(date.strftime("%Y-%m-%d"))

for game, roster in rosters.items():
    analyses = []
    print(f"----------Analyzing matchups for {game}----------")
    analyses += mas.analyze_player_matchups(roster["away"], roster["home"])
    analyses += mas.analyze_player_matchups(roster["home"], roster["away"])
    print(f"-------------------------------------------------\n")
    for analysis in analyses:
        player_name = " ".join(unidecode(ps.index_to_player(analysis.player_index).name).replace("'", " ").replace("-", " ").split(" ")[:2]).lower()
        if player_name not in prop_lines:
            continue
        player_odds = PlayerOdds(analysis.player_index, date)
        for stat, prop_line in prop_lines.items():
            player_odds.add_prop_line(stat, prop_line)

        points_diff = round(analysis.prediction.points - prop_lines[player_name]["points"].line, 2)
        rebounds_diff = round(analysis.prediction.rebounds - prop_lines[player_name]["rebounds"].line, 2)
        assits_diff = round(analysis.prediction.assists - prop_lines[player_name]["assists"].line, 2)
        print(f"[{player_name:<20}]:\tPTS:{points_diff:<8} REB:{rebounds_diff:<8} AST:{assits_diff:<8}")
    print(f"-------------------------------------------------\n")
