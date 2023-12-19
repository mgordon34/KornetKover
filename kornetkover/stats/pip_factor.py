class PipFactor(object):
    def __init__(
        self,
        player_index: str,
        defender_index: str,
        num_games: int,
        minutes: float,
        points: float,
        rebounds: float,
        assists: float,
    ) -> None:
        self.player_index = player_index
        self.defender_index = defender_index
        self.num_games = num_games
        self.minutes= minutes
        self.points= points
        self.rebounds= rebounds
        self.assists= assists

    def to_db(self) -> tuple:
        return (
            self.player_index,
            self.defender_index,
            self.num_games,
            self.minutes,
            self.points,
            self.rebounds,
            self.assists,
        )
