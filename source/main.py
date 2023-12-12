from source.tools.db import DB
from source.tools.scraper import Scraper
from source.stats.player_stat_service import PlayerStatService

db = DB()
db.initialize_tables()
pss = PlayerStatService(db)

rosters = Scraper.get_rosters_for_upcoming_games()

for game, roster in rosters.items():
    print(f"----------Analyzing matchups for {game}----------")
    pss.analyze_player_matchups(roster["away"], roster["home"])
    pss.analyze_player_matchups(roster["home"], roster["away"])
    print(f"-------------------------------------------------\n")