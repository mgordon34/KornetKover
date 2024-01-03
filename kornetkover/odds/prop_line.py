from datetime import datetime

class PropLine(object):
    def __init__(self, stat: str, line: float, over_odds: str, under_odds: str):
        self.stat = stat
        self.line = line
        self.over_odds = over_odds
        self.under_odds = under_odds

    def to_db(self):
        return (self.stat, self.line, self.over_odds, self.under_odds)
