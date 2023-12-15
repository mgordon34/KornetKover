from datetime import datetime

class PlayerAnalysis(object):
    def __init__(self, player_index: str, date: datetime.date) -> None:
        self.player_index = player_index
        self.date = date
        self.pip_factors = []
        self.prediction = None

    def add_pip_factor(self, pip_factor):
        self.pip_factors.append(pip_factor)
