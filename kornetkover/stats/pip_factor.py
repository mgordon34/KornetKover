from enum import Enum

class RelationshipType(Enum):
    TEAMMATE = "teammate"
    OPPONENT = "opponent"


class PipFactor(object):
    def __init__(
        self,
        primary_index: str,
        other_index: str,
        relationship: RelationshipType, 
        num_games: int,
        minutes: float,
        points: float,
        rebounds: float,
        assists: float,
    ) -> None:
        self.primary_index = primary_index
        self.other_index = other_index
        self.relationship = relationship
        self.num_games = num_games
        self.minutes= minutes
        self.points= points
        self.rebounds= rebounds
        self.assists= assists

    def to_db(self) -> tuple:
        return (
            self.primary_index,
            self.other_index,
            self.relationship,
            self.num_games,
            self.minutes,
            self.points,
            self.rebounds,
            self.assists,
        )