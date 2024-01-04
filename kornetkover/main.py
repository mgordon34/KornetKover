from unidecode import unidecode

from kornetkover.analysis.matchup_analysis_service import MatchupAnalysisService
from kornetkover.tools.db import DB
from kornetkover.players.player_service import PlayerService
from kornetkover.players.player import Player
from kornetkover.stats.player_stat_service import PlayerStatService
from kornetkover.tools.scraper import Scraper

db = DB()
db.initialize_tables()
mas = MatchupAnalysisService(db)
ps = PlayerService(db)

rosters = Scraper.get_rosters_for_upcoming_games()
for roster in rosters:
    print(rosters[roster])

prop_lines = Scraper.get_prop_lines("2024-01-04")

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

        points_diff = analysis.prediction.points - prop_lines[player_name]["points"].line
        rebounds_diff = analysis.prediction.rebounds - prop_lines[player_name]["rebounds"].line
        assits_diff = analysis.prediction.assists - prop_lines[player_name]["assists"].line
        print(f"[{player_name}]: PTS:{points_diff} REB:{rebounds_diff} AST:{assits_diff}")
    print(f"-------------------------------------------------\n")
