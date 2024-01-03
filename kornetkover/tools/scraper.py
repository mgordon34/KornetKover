from collections import defaultdict
import time

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import requests
from unidecode import unidecode

from kornetkover.stats.prop_line import PropLine
from kornetkover.tools.db import DB

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
            name = unidecode(basic_stats[i].find("th").find("a").text)
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
    def _scrape_playing_players(cls, team, missing_players=[]):
        time.sleep(4)
        url = "https://www.basketball-reference.com/teams/{}/2024.html"
        page = requests.get(url.format(team))
        soup = BeautifulSoup(page.content, "html.parser")
        player_soup = soup.find(id="per_game").find("tbody").find_all("tr")

        players = {"starting": [], "bench": []}
        i = 0
        for player in player_soup:
            index = player.find("a")["href"].split("/")[3].split(".")[0]
            avg_min = cls._get_avg_minutes_from_player_tr(player)
            if index not in missing_players:
                if avg_min > 20 and len(players["starting"]) <= 5:
                    players["starting"].append(index)
                elif avg_min > 10:
                    players["bench"].append(index)
            else:
                print(f"{index} is OUT, skipping...")

        return players

    @classmethod
    def _get_avg_minutes_from_player_tr(cls, player_tr):
        for column in player_tr.find_all("td"):
            if column.has_attr("data-stat") and column["data-stat"] == "mp_per_g":
                return float(column.text)

    @classmethod
    def _get_missing_players(cls):
        url = "https://www.basketball-reference.com/friv/injuries.fcgi"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        missing_players = defaultdict(lambda: {"out":[],"dtd":[]})
        players = soup.find(id="injuries").find("tbody").find_all("tr")
        for player in players:
            index = player.find("th")["data-append-csv"]
            data = player.find_all("td")
            team = data[0].find("a")["href"].split("/")[2]
            status = data[2].text
            if status.startswith("Out"):
                missing_players[team]["out"].append(index)
            elif status.startswith("Day To Day"):
                missing_players[team]["dtd"].append(index)

        return missing_players

    @classmethod
    def get_rosters_for_upcoming_games(cls):
        game_list = cls.scrape_upcoming_games()
        missing_players = cls._get_missing_players()

        games = {}
        for game in game_list:
            away_players = cls._scrape_playing_players(game[0], missing_players[game[0]]["out"])
            home_players = cls._scrape_playing_players(game[1], missing_players[game[1]]["out"])

            games[game[0] + game[1]] = {
                "away": {**away_players, **missing_players[game[0]]},
                "home": {**home_players, **missing_players[game[1]]},
            }

        return games

    @classmethod
    def get_prop_lines(cls, date_str: str) -> dict:
        game_urls = cls.get_covers_games_for_date(date_str)

        prop_lines = {}
        for game_url in game_urls:
            player_urls = cls.get_covers_players_for_game(game_url)
            for player_url in player_urls:
                player_name = " ".join(player_url.split("/")[6].split("-")[:2])
                player_prop = cls.get_prop_lines_for_player(player_url)
                if player_prop:
                    prop_lines[player_name] = player_prop

        return prop_lines

    @classmethod
    def get_covers_games_for_date(cls, date_str: str) -> list[str]:
        url = f"https://www.covers.com/sports/nba/matchups?selectedDate={date_str}"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        games = soup.find_all("div", class_="cmg_matchup_game_box")

        game_urls = []
        for game in games:
            game_urls.append(game.find("div", class_="__right_col").find("a")["href"])

        return game_urls

    @classmethod
    def get_covers_players_for_game(cls, game_url: str) -> list[str]:
        url = f"https://www.covers.com/{game_url}/props"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        players = soup.find_all("div", class_="player-headshot-name")

        player_urls = []
        for player in players:
            player_urls.append(player.find("a")["href"])

        return player_urls

    @classmethod
    def get_prop_lines_for_player(cls, player_url: str) -> dict[PropLine]:
        print(f"getting prop lines for {player_url}")
        prop_names = {
            "points": "points-scored",
            "rebounds": "total-rebounds",
            "assists": "total-assists",
            "points-rebounds-assists": "total-points,-rebounds,-and-assists",
            "points-rebounds": "points-and-rebounds",
            "points-assists": "points-and-assists",
            "rebounds-assists": "rebounds-and-assists",
        }

        url = f"https://www.covers.com/{player_url}"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        prop_lines = {}
        for stat, prop_name in prop_names.items():
            lines = soup.find(id=prop_name)
            if not lines:
                return None
            over_block = lines.find_all("div", class_=f"other-over-odds")[1].find("div", class_="odds").text.split()
            under_block = lines.find_all("div", class_=f"other-under-odds")[1].find("div", class_="odds").text.split()

            line = float(over_block[0][1:])
            over_odds = over_block[1]
            under_odds = under_block[1]

            prop_lines[stat] = PropLine(stat, line, over_odds, under_odds)

        return prop_lines

def _convert_mp(mp_string):
    (m, s) = mp_string.split(":")
    return int(m) + round(int(s)/60, 2)

def _normalize_stat(stat):
    if not stat:
        return 0
    return stat


if __name__ == "__main__":
    db = DB()

    db.initialize_tables()
    # start_date = datetime.strptime('2018-10-10', '%Y-%m-%d').date()
    # end_date = datetime.strptime('2023-12-17', '%Y-%m-%d').date()
    # Scraper.scrape_games(start_date, end_date, db)

    # teams = [('ATL', 'Atlanta Hawks'), ('BOS', 'Boston Celtics'), ('BRK', 'Brooklyn Nets'), ('CHO', 'Charlotte Hornets'), ('CHI', 'Chicago Bulls'), ('CLE', 'Cleveland Cavaliers'), ('DAL', 'Dallas Mavericks'), ('DEN', 'Denver Nuggets'), ('DET', 'Detroit Pistons'), ('GSW', 'Golden State Warriors'), ('HOU', 'Houston Rockets'), ('IND', 'Indiana Pacers'), ('LAC', 'Los Angeles Clippers'), ('LAL', 'Los Angeles Lakers'), ('MEM', 'Memphis Grizzlies'), ('MIA', 'Miami Heat'), ('MIL', 'Milwaukee Bucks'), ('MIN', 'Minnesota Timberwolves'), ('NOP', 'New Orleans Pelicans'), ('NYK', 'New York Knicks'), ('OKC', 'Oklahoma City Thunder'), ('ORL', 'Orlando Magic'), ('PHI', 'Philadelphia 76ers'), ('PHO', 'Phoenix Suns'), ('POR', 'Portland Trail Blazers'), ('SAC', 'Sacramento Kings'), ('SAS', 'San Antonio Spurs'), ('TOR', 'Toronto Raptors'), ('UTA', 'Utah Jazz'), ('WAS', 'Washington Wizards')]
    # db.add_teams(teams)

    today = datetime.now().strftime("%Y-%m-%d")
    print(today)
    props = Scraper.get_prop_lines('2024-01-03')
    for player, prop in props.items():
        print(f"{player}--------------------")
        for k, v in prop.items():
            print(v.__dict__)

    db.close()
