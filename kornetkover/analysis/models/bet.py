from datetime import datetime

from kornetkover.stats.models.player import Player
from kornetkover.odds.player_odds import PropLine

class Bet(object):
    def __init__(self, player: Player, line: PropLine, date: datetime.date, side: str, actual: int, result: str):
        self.player = player
        self.line = line
        self.date = date
        self.side = side
        self.actual = actual
        self.result = result
