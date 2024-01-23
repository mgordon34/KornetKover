
class Player(object):
    def __init__(self, index: str, name: str, cur_team: str=None):
        self.index = index
        self.name = name
        self.cur_team = cur_team
