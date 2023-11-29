import logging

import psycopg2, psycopg2.extras

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
                date DATE NOT NULL
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
                minutes REAL NOT NULL,
                points INT NOT NULL,
                rebounds INT NOT NULL,
                assists INT NOT NULL,
                ortg INT NOT NULL,
                drtg INT NOT NULL
            )""")

        for command in commands:
            cur.execute(command)
        self.conn.commit()
        cur.close()

    def add_teams(self, teams):
        sql = """INSERT INTO teams(index, name) VALUES %s"""

        count = 0
        try:
            cur = self.conn.cursor()
            psycopg2.extras.execute_values(cur, sql, teams)
        except(Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            count = cur.rowcount
            self.conn.commit()
            cur.close()

        return count

    def add_games(
        self,
        games
    ):
        sql = """INSERT INTO games(home_index, away_index, home_score, away_score, date)
                 VALUES %s"""

        count = 0
        try:
            cur = self.conn.cursor()
            psycopg2.extras.execute_values(cur, sql, games)
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
    db.close()
