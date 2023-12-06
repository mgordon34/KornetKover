
class PlayerStat(object):
    def __init__(
        self,
        frame: int,
        num_games: int,
        minutes: float,
        points: float,
        rebounds: float,
        assists: float
    ) -> None:
        self.frame = frame
        self.num_games = num_games
        self.minutes = minutes
        self.points = points
        self.rebounds = rebounds
        self.assists = assists
