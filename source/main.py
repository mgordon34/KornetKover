from source.tools.db import DB
from source.tools.scraper import Scraper
from source.stats.player_stat_service import PlayerStatService
from source.analysis.matchup_analysis_service import MatchupAnalysisService

db = DB()
db.initialize_tables()
mas = MatchupAnalysisService(db)

rosters = Scraper.get_rosters_for_upcoming_games()

for game, roster in rosters.items():
    print(f"----------Analyzing matchups for {game}----------")
    mas.analyze_player_matchups(roster["away"], roster["home"])
    mas.analyze_player_matchups(roster["home"], roster["away"])
    print(f"-------------------------------------------------\n")