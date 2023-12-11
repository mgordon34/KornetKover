from source.stats.player_stat import PlayerStat

class PipFactor(object):
    def __init__(
        self,
        player_index: str,
        defender_index: str,
        player_stat: PlayerStat,
    ) -> None:
        self.player_index = player_index
        self.defender_index = defender_index
        self.player_stat = player_stat

    def to_db(self) -> tuple:
        return (
            self.player_index,
            self.defender_index,
            self.player_stat.frame,
            self.player_stat.num_games,
            self.player_stat.minutes,
            self.player_stat.points,
            self.player_stat.rebounds,
            self.player_stat.assists,
            self.player_stat.ortg,
            self.player_stat.drtg,
        )
