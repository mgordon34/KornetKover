
class Player(object):
    def __init__(self, index: str, name: str, teams: {}=None):
        self.index = index
        self.name = name
        self.teams = teams
