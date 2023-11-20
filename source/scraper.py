from bs4 import BeautifulSoup
import requests

from db import DB

class Scraper(object):
    @classmethod
    def get_team_indexes(cls):
        url = "https://www.basketball-reference.com/teams/"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        active_teams = soup.find(id="all_teams_active")
        full_team_row = active_teams.find_all("tr", class_="full_table")
        teams = []
        for row in full_team_row:
            team_dict = {}
            team = row.find("th")
            team_dict["name"] = team.text
            team_dict["index"] = team.find("a")["href"].split("/")[2]
            teams.append(team_dict)

        return teams

if __name__ == "__main__":
    db = DB()
    db.initialize_tables()
    teams = Scraper.get_team_indexes()
    for team in teams:
        db.add_team(team["index"], team["name"])