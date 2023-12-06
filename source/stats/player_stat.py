
class PlayerStat(object):
    def __init__(self, num_games: int, points: float, rebounds: float, assists: float) -> None:
        self.num_games = num_games
        self.points = points
        self.rebounds = rebounds
        self.assists = assists