import time

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests

from source.tools.db import DB

base_url = "https://www.basketball-reference.com"

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
    def scrape_games(cls, start_date, end_date, db=None):
        url = "https://www.basketball-reference.com/boxscores/?month={0}&day={1}&year={2}"
        cur_date = start_date
        while cur_date <= end_date:
            print(f"scraping for {cur_date}")
            time.sleep(4)
            page = requests.get(url.format(cur_date.month, cur_date.day, cur_date.year))
            soup = BeautifulSoup(page.content, "html.parser")
            games = soup.find_all("td", class_="gamelink")
            print(f"{len(games)} games found")

            for game in games:
                time.sleep(4)
                game_string = game.find("a")["href"]
                cls._scrape_game(game_string, cur_date, db)

            print("--------------------------")

            cur_date += timedelta(days=1)

    @classmethod
    def _scrape_game(cls, game_string, date, db):
        print(f"scraping game for {game_string}")
        page = requests.get(base_url + game_string)
        soup = BeautifulSoup(page.content, "html.parser")

        scorebox = soup.find("div", class_="scorebox")
        away_index, home_index = [team.find("a")["href"].split("/")[2] for team in scorebox.find_all("strong")]
        away_score, home_score = [int(team.text) for team in scorebox.find_all("div", class_="score")]
        game_id = db.add_game((home_index, away_index, home_score, away_score, date))


        (home_players, home_stats) = cls._scrape_player_stats(soup, game_id, home_index)
        (away_players, away_stats) = cls._scrape_player_stats(soup, game_id, away_index)

        db.add_players(home_players + away_players)
        db.add_player_games(home_stats + away_stats)

    @classmethod
    def _scrape_player_stats(cls, soup, game_id, team_index):
        basic_stats = soup.find(id=f"box-{team_index}-game-basic").find("tbody").find_all("tr")
        advanced_stats = soup.find(id=f"box-{team_index}-game-advanced").find("tbody").find_all("tr")

        players = []
        player_games = []
        for i in range(0, len(basic_stats)):
            if i == 5 or basic_stats[i].find("td", {"data-stat": "reason"}):
                continue

            index = (basic_stats[i].find("th")["data-append-csv"])
            name = basic_stats[i].find("th").find("a").text
            minutes = _convert_mp(basic_stats[i].find("td", {"data-stat": "mp"}).text)
            rebounds = _normalize_stat(basic_stats[i].find("td", {"data-stat": "trb"}).text)
            assists = _normalize_stat(basic_stats[i].find("td", {"data-stat": "ast"}).text)
            points = _normalize_stat(basic_stats[i].find("td", {"data-stat": "pts"}).text)
            ortg = _normalize_stat(advanced_stats[i].find("td", {"data-stat": "off_rtg"}).text)
            drtg = _normalize_stat(advanced_stats[i].find("td", {"data-stat": "def_rtg"}).text)

            players.append((index, name))
            player_games.append((index, game_id, team_index, minutes, points, rebounds, assists, ortg, drtg))

        return (players, player_games)

    @classmethod
    def scrape_upcoming_games(cls, date=None):
        url = "https://www.basketball-reference.com/leagues/NBA_2024_games-{}.html"
        if not date:
            date = datetime.now().date()

        page = requests.get(url.format(date.strftime("%B").lower()))
        soup = BeautifulSoup(page.content, "html.parser")
        game_soup = soup.find(id="schedule").find("tbody").find_all("tr")

        games = []
        for game in game_soup:
            date_string = game.find("th").get("csk")
            game_date = datetime.strptime(date_string[:-4], "%Y%m%d").date()
            if game_date != date:
                continue

            games.append([team["href"].split("/")[2] for team in game.find_all("a")[1:]])

        return games

    @classmethod
    def _scrape_starting_five(cls, team, missing_players=[]):
        time.sleep(4)
        url = "https://www.basketball-reference.com/teams/{}/2024.html"
        page = requests.get(url.format(team))
        soup = BeautifulSoup(page.content, "html.parser")
        player_soup = soup.find(id="per_game").find("tbody").find_all("tr")

        players = []
        i = 0
        while len(players) < 5:
            index = player_soup[i].find("a")["href"].split("/")[3].split(".")[0]
            if index not in missing_players:
                players.append(index)
            i += 1

        return players

    @classmethod
    def get_rosters_for_upcoming_games(cls):
        game_list = cls.scrape_upcoming_games()

        games = {}
        for game in game_list:
            away_players = cls._scrape_starting_five(game[0])
            home_players = cls._scrape_starting_five(game[1])

            games[game[0] + game[1]] = {
                "away": away_players,
                "home": home_players,
            }

        return games

def _convert_mp(mp_string):
    (m, s) = mp_string.split(":")
    return int(m) + round(int(s)/60, 2)

def _normalize_stat(stat):
    if not stat:
        return 0
    return stat


if __name__ == "__main__":
    db = DB()

    # db.initialize_tables()
    # start_date = datetime.strptime('2023-10-20', '%Y-%m-%d').date()
    # end_date = datetime.strptime('2023-12-03', '%Y-%m-%d').date()
    # Scraper.scrape_games(start_date, end_date, db)

    games = Scraper.get_rosters_for_upcoming_games()
    for game, roster in games.items():
        print(f"---------{game}---------")
        print(roster["away"])
        print(roster["home"])

    db.close()
