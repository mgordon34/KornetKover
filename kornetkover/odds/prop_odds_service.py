from collections import defaultdict
from datetime import datetime
import json
from typing import List

import requests

from kornetkover.config import config
from kornetkover.odds.odds_service import OddsService
from kornetkover.odds.prop_line import PropLine
from kornetkover.odds.player_odds import PlayerOdds
from kornetkover.stats.services.player_service import PlayerService
from kornetkover.tools.db import DB

class PropOddsService(object):
    base_url = "https://api.prop-odds.com"
    base_params = {
        "api_key": config.prop_odds_key,
        "tz": "America/New_York",
    }

    def __init__(self, db: DB) -> None:
        self.db = db

    def get_game_ids_for_date(self, date: datetime.date) -> List[str]:
        endpoint = "/beta/games/nba"
        params = self.base_params
        params["date"] = date.strftime("%Y-%m-%d"),

        res = requests.get(self.base_url + endpoint, params=params)
        json_res = json.loads(res.content)

        return [game["game_id"] for game in json_res["games"]]

    def get_markets_for_game(self, game_id: str) -> List[str]:
        endpoint = f"/beta/markets/{game_id}"

        res = requests.get(self.base_url + endpoint, params=self.base_params)
        json_res = json.loads(res.content)

        return [market["name"] for market in json_res["markets"]]


    def get_odds_for_market(self, game_id: str, market: str) -> List[PropLine]:
        endpoint = f"/beta/odds/{game_id}/{market}"
        ps = PlayerService(self.db)

        res = requests.get(self.base_url + endpoint, params=self.base_params)
        json_res = json.loads(res.content)

        player_lines = defaultdict(dict)
        for sportsbook in json_res["sportsbooks"]:
            if sportsbook["bookie_key"] != "caesars":
                continue

            for outcome in sportsbook["market"]["outcomes"]:
                player_name = " ".join(outcome["description"].split(" ")[:-2])
                timestamp = datetime.strptime(outcome["timestamp"], "%Y-%m-%dT%H:%M:%S")

                player = ps.name_to_player(player_name)
                if not player:
                    print(f"Could not match {player_name} to database")
                    continue


                if self._should_add_line(outcome["name"], timestamp, player_lines[player.index]):
                    player_lines[player.index][outcome["name"]] = {
                        "timestamp": timestamp,
                        "line": outcome["handicap"],
                        "odds": outcome["odds"],
                    }

        return player_lines

        player_odds = []
        for player_index, lines in player_lines:
            player_odds.append(self._create_player_odds(player_index, lines, True))


        return player_odds

    def _should_add_line(self, bet_type: str, timestamp: datetime, player_line: dict) -> bool:
        if bet_type not in player_line:
            return True

        if timestamp > player_line[bet_type]["timestamp"]:
            return True

        return False

    def create_player_odds(self, player_lines: dict, stat: str, date: datetime.date) -> PlayerOdds:
        all_player_odds = []
        for player_index, line in player_lines.items():
            player_odds = PlayerOdds(player_index, date)

            prop_line = PropLine(stat, line["Over"]["line"], line["Over"]["odds"], line["Under"]["odds"])
            player_odds.add_prop_line(prop_line)

            all_player_odds.append(player_odds)

        os = OddsService(self.db)
        for player_odds in all_player_odds:
            os.add_player_odds(player_odds.to_db())

        return all_player_odds
            

if __name__ == "__main__":
    db = DB()
    pos = PropOddsService(db)

    date = datetime.strptime("2024-01-15", "%Y-%m-%d")
    # game_ids = pos.get_game_ids_for_date(date)
    # print(game_ids)
    # markets = pos.get_markets_for_game(game_ids[0])
    # print(markets)
    lines = pos.get_odds_for_market("054c3a2b4085ee4c6b2ac933cd129d97", "player_points_over_under")
    odds = pos.create_player_odds(lines, "points", date)

    for odd in odds:
        print(f"{odd.player_index}: {[line.to_db() for line in odd.prop_lines]}")
