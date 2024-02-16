from datetime import datetime

from kornetkover.analysis.matchup_analysis_service import MatchupAnalysisService
from kornetkover.stats.services.player_service import PlayerService
from kornetkover.stats.services.game_service import GameService
from kornetkover.tools.db import DB

class AnalysisRunner(object):
    def __init__(self, db: DB) -> None:
        self.db = db
        self.gs = GameService(db)
        self.mas = MatchupAnalysisService(db)
        self.ps = PlayerService(db)

    def run_analysis(self, date: datetime.date):
        # TODO: Here is where we can specify a strategy to run in the future
        all_player_analyses = []

        games = self.gs.get_games_for_date(date)
        missing_players = self.ps.get_missing_player_indexes(date)

        for game in games:
            away_roster = self.ps.find_roster_for_team(game, game.away_index, missing_players)
            home_roster = self.ps.find_roster_for_team(game, game.home_index, missing_players)

            # print(f"---------------{game.away_index} vs {game.home_index}---------------")
            all_player_analyses += self.mas.get_player_analyses_per_team(game, game.away_index, away_roster, home_roster)
            all_player_analyses += self.mas.get_player_analyses_per_team(game, game.home_index, home_roster, away_roster)
            # print("----------------------------------------\n")

        return all_player_analyses

if __name__ == "__main__":
    db = DB()
    ar = AnalysisRunner(db)

    date = datetime.strptime("2024-01-16", "%Y-%m-%d")

    ar.run_analysis(date)
