from datetime import datetime
from typing import List

from kornetkover.players.player_service import PlayerService
from kornetkover.tools.db import DB
from kornetkover.tools.scraper import Scraper
from kornetkover.odds.prop_line import PropLine


class OddsService(object):
    def __init__(self, db: DB):
        self.db = db

    def to_player_odds(self, player_index: str, date: datetime.date, prop_lines: List[PropLine]):
        player_odds = []
        for prop_line in prop_lines:
            player_odds.append((player_index, date.strftime("%Y-%m-%d"), prop_line.stat, prop_line.line, prop_line.over_odds, prop_line.under_odds))

        return player_odds

    def add_player_odds(self, player_odds):
        sql = """INSERT INTO player_odds(player_index, date, stat, line, over_odds, under_odds)
                 VALUES %s
                 ON CONFLICT (player_index, stat, date) DO UPDATE SET
                 line = EXCLUDED.line, over_odds = EXCLUDED.over_odds, under_odds = EXCLUDED.under_odds"""

        return self.db._bulk_insert(sql, player_odds)

    def get_player_odds(self, player_index: str, date: datetime.date):
        sql = """SELECT player_index, date, stat, line, over_odds, under_odds
                 FROM player_odds
                 WHERE player_index='{0}' AND date='{1}'"""
        
        return self.db.execute_query(sql.format(player_index, date))

    def update_player_odds_for_date(self, date: datetime.date):
        ps = PlayerService(self.db)
        prop_lines = Scraper.get_prop_lines(date)
        
        for name, lines in prop_lines.items():
            player = ps.name_to_player(name)
            if not player:
                print(f"name lookup failed for {name}")
                continue

            index = player.index
            player_odds = self.to_player_odds(index, date, lines.values())

            self.add_player_odds(player_odds)


if __name__ == "__main__":
    db = DB()
    db.initialize_tables()
    os = OddsService(db)
    ps = PlayerService(db)

    date = datetime.now().date()
    os.update_player_odds_for_date(date)

    print(os.get_player_odds("caldwke01", date))
