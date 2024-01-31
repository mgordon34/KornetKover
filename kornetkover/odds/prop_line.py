from datetime import datetime

class PropLine(object):
    def __init__(self, stat: str, line: float, over_odds: str, under_odds: str):
        self.stat = stat
        self.line = line
        self.over_odds = over_odds
        self.under_odds = under_odds
        self.predicted_delta = None

    def add_predicted_delta(self, predicted_delta: float) -> None:
        self.predicted_delta = predicted_delta

    def get_odds(self) -> int:
        if not self.predicted_delta:
            return None

        if self.predicted_delta >=0:
            return int(self.over_odds)
        
        return int(self.under_odds)

    def to_db(self):
        return (self.stat, self.line, self.over_odds, self.under_odds)
