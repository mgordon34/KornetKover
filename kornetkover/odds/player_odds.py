from typing import List

from datetime import datetime

from kornetkover.odds.prop_line import PropLine

class PlayerOdds(object):
    def __init__(self, player_index: str, date: datetime.date) -> None:
        self.player_index = player_index
        self.date = date
        
        self.prop_lines = []

    def add_prop_line(self, prop_line: PropLine) -> None:
        self.prop_lines.append(prop_line)

    def to_db(self) -> List[tuple]:
        db_objs = []

        for prop_line in self.prop_lines:
            db_objs.append((self.player_index, self.date, prop_line.stat, prop_line.line,
                            prop_line.over_odds, prop_line.under_odds))

        return db_objs

