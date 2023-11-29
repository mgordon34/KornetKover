from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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
            name = team.text
            index = team.find("a")["href"].split("/")[2]

            teams.append((index, name))

        return teams

    @classmethod
    def scrape_games(cls, start_date, end_date):
        url = "https://www.basketball-reference.com/boxscores/?month=%s&day=%s&year=%s"
        cur_date = start_date
        while cur_date <= end_date:
            print(f"scraping for {cur_date}")
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            games = soup.find_all("div", "game_summary")
            for game in games:
                print(game)

            cur_date += timedelta(days=1)


if __name__ == "__main__":
    # db = DB()
    start_date = datetime.strptime('2023-04-21', '%Y-%m-%d').date()
    end_date = datetime.strptime('2023-04-21', '%Y-%m-%d').date()
    Scraper.scrape_games(start_date, end_date)
