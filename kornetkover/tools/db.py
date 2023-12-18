import logging
import traceback

import psycopg2, psycopg2.extras
from datetime import datetime

logger = logging.getLogger(__name__)

class DB(object):
    def __init__(self):
        self.conn = self.create_connection()

    def create_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(
                database="kornet_kover",
                host="localhost",
                user="postgres",
                password="password",
                port="5432"
            )
            logger.info("DB connection successful")
        except Exception as e:
            print(e)
            logger.error(e)
        return conn

    def close(self):
        self.conn.close()

    def initialize_tables(self):
        cur = self.conn.cursor()
        commands = []
        commands.append("""
            CREATE TABLE IF NOT EXISTS teams (
                index VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            )""")
        commands.append("""
            CREATE TABLE IF NOT EXISTS games (
                id SERIAL PRIMARY KEY,
                home_index VARCHAR(255) REFERENCES teams(index),
                away_index VARCHAR(255) REFERENCES teams(index),
                home_score INT NOT NULL,
                away_score INT NOT NULL,
                date DATE NOT NULL,
                CONSTRAINT uq_games UNIQUE(date, home_index)
            )""")
        commands.append("""
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                index VARCHAR(20) UNIQUE,
                name VARCHAR(255)
            )""")
        commands.append("""
            CREATE TABLE IF NOT EXISTS player_games (
                id SERIAL PRIMARY KEY,
                player_index VARCHAR(20) REFERENCES players(index),
                game INT REFERENCES games(id),
                team_index VARCHAR(255) REFERENCES teams(index),
                minutes REAL NOT NULL,
                points INT NOT NULL,
                rebounds INT NOT NULL,
                assists INT NOT NULL,
                ortg INT NOT NULL,
                drtg INT NOT NULL,
                CONSTRAINT uq_player_games UNIQUE(player_index, game)
            )""")
        commands.append("""
            CREATE TABLE IF NOT EXISTS pip_factors (
                id SERIAL PRIMARY KEY,
                player_index VARCHAR(20) REFERENCES players(index),
                defender_index VARCHAR(20) REFERENCES players(index),
                frame INT NOT NULL,
                game_count INT NOT NULL,
                minutes REAL NOT NULL,
                points REAL NOT NULL,
                rebounds REAL NOT NULL,
                assists REAL NOT NULL,
                CONSTRAINT uq_pip_index UNIQUE(player_index, defender_index)
            )""")

        for command in commands:
            cur.execute(command)
        self.conn.commit()
        cur.close()

    def add_teams(self, teams):
        sql = """INSERT INTO teams(index, name) VALUES %s"""

        return self._bulk_insert(sql, teams)

    def add_games(self, games):
        sql = """INSERT INTO games(home_index, away_index, home_score, away_score, date)
                 ON CONFLICT (date, home_index) DO NOTHING
                 VALUES %s"""

        return self._bulk_insert(sql, games)

    def execute_query(self, query):
        res = None

        try:
            cur = self.conn.cursor()
            cur.execute(query)
            res = cur.fetchall()
        except(Exception, psycopg2.DatabaseError) as error:
            print(traceback.format_exc())
        finally:
            self.conn.commit()
            cur.close()

        return res

    def add_game(self, game):
        sql = """INSERT INTO games(home_index, away_index, home_score, away_score, date)
                 VALUES (%s,%s,%s,%s,%s)
                 ON CONFLICT (date, home_index) DO UPDATE SET date=EXCLUDED.date
                 RETURNING id"""

        id = None
        try:
            cur = self.conn.cursor()
            cur.execute(sql, game)
            id = cur.fetchone()[0]
        except(Exception, psycopg2.DatabaseError) as error:
            print(traceback.format_exc())
        finally:
            self.conn.commit()
            cur.close()

        return id


    def add_players(self, players):
        sql = """INSERT INTO players(index, name)
                 VALUES %s
                 ON CONFLICT (index) DO NOTHING"""

        return self._bulk_insert(sql, players)

    def add_player_games(self, player_games):
        sql = """INSERT INTO player_games(player_index, game, team_index, minutes, points,
                 rebounds, assists, ortg, drtg)
                 VALUES %s
                 ON CONFLICT (player_index, game) DO NOTHING"""

        return self._bulk_insert(sql, player_games)

    def add_pip_factors(self, pip_factors):
        sql = """INSERT INTO pip_factors(player_index, defender_index, frame, game_count,
                 minutes, points, rebounds, assists)
                 VALUES %s
                 ON CONFLICT (player_index, defender_index) DO NOTHING"""

        return self._bulk_insert(sql, pip_factors)

    def _bulk_insert(self, sql, objects):
        count = 0
        try:
            cur = self.conn.cursor()
            psycopg2.extras.execute_values(cur, sql, objects)
        except(Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            count = cur.rowcount
            self.conn.commit()
            cur.close()

        return count

    def get_games(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * from games;")
        res = cur.fetchall()

        cur.close()
        return res

if __name__ == "__main__":
    db = DB()
    db.initialize_tables()

    print(db.get_games())

    db.close()
