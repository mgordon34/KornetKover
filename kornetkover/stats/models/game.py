from typing import Optional

from datetime import datetime

class Game(object):
    def __init__(self,
        id: int,
        home_index: str,
        away_index:str,
        date: datetime.date,
        home_score: Optional[int] = None,
        away_score: Optional[int] = None,
    ) -> None:
        self.id = id
        self.home_index = home_index
        self.away_index = away_index
        self.date = date
        self.home_score = home_score
        self.away_score = away_score

