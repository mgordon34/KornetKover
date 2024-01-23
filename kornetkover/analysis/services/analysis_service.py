from datetime import datetime

from kornetkover.analysis.matchup_analysis_service import MatchupAnalysisService
from kornetkover.odds.odds_service import OddsService
from kornetkover.stats.services.player_service import PlayerService
from kornetkover.stats.services.game_service import GameService
from kornetkover.tools.db import DB

class AnalysisRunner(object):
    def __init__(self, db: DB) -> None:
        self.db = db
        self.gs = GameService(db)
        self.mas = MatchupAnalysisService(db)
        self.os = OddsService(db)
        self.ps = PlayerService(db)

    def run_analysis(self, date: datetime.date):
        # TODO: Here is where we can specify a strategy to run in the future

        games = self.gs.get_games_for_date(date)
        # player_odds = self.os.get_player_odds(player.index, date)

        game_data = []
        for game in games:

            away_roster = self.ps.find_roster_for_game(game.id, game.away_index)
            home_roster = self.ps.find_roster_for_game(game.id, game.home_index)
            game_data.append(
                {
                    "game": game,
                    "away_roster": away_roster,
                    "home_roster": home_roster,
                }
            )

            all_player_analyses = []
            all_player_analyses += self.mas.get_player_analyses_per_team(game, game.away_index, away_roster, home_roster)
            all_player_analyses += self.mas.get_player_analyses_per_team(game, game.home_index, home_roster, away_roster)


        return

if __name__ == "__main__":
    db = DB()
    ar = AnalysisRunner(db)

    date = datetime.strptime("2024-01-16", "%Y-%m-%d")

    ar.run_analysis(date)
