from datetime import datetime

from kornetkover.stats.player_per import PlayerPer

class PlayerAnalysis(object):
    def __init__(self, player_index: str, date: datetime.date, yearly_avg_per: PlayerPer) -> None:
        self.player_index = player_index
        self.date = date
        self.yearly_avg_per = yearly_avg_per
        self.pip_factors = []
        self.notable_stats = []
        self.prediction = None

    def add_pip_factor(self, pip_factor):
        self.pip_factors.append(pip_factor)
