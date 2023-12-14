from source.stats.player_per import PlayerPer

class PipFactor(object):
    def __init__(
        self,
        player_index: str,
        defender_index: str,
        player_per: PlayerPer,
    ) -> None:
        self.player_index = player_index
        self.defender_index = defender_index
        self.player_per = player_per

    def to_db(self) -> tuple:
        return (
            self.player_index,
            self.defender_index,
            self.player_per.frame,
            self.player_per.num_games,
            self.player_per.minutes,
            self.player_per.points,
            self.player_per.rebounds,
            self.player_per.assists,
        )
