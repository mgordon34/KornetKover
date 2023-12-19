from datetime import datetime

class PlayerStat(object):
    def __init__(
        self,
        minutes: float,
        points: float,
        rebounds: float,
        assists: float,
        date: datetime.date=None,
    ) -> None:
        self.minutes = minutes
        self.points = points
        self.rebounds = rebounds
        self.assists = assists
        self.date = date
