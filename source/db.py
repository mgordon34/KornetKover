import logging

import psycopg2

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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id SERIAL PRIMARY KEY,
                home_team VARCHAR(255) NOT NULL,
                away_team VARCHAR(255) NOT NULL,
                home_score INT NOT NULL,
                away_score INT NOT NULL,
                date DATE NOT NULL
            )""")
        cur.close()
        self.conn.commit()

    def add_game(
        self,
        home_team,
        away_team,
        home_score,
        away_score, 
        date
    ):
        sql = """INSERT INTO games(home_team, away_team, home_score, away_score, date)
                 VALUES(%s, %s, %s, %s, %s) RETURNING id"""
        try:
            cur = self.conn.cursor()
            cur.execute(sql, (home_team, away_team, home_score, away_score, date))
            id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
        except(Exception, psycopg2.DatabaseError) as error:
            print(error)
        return id
        
    def get_games(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * from games;")
        res = cur.fetchall()

        cur.close()
        return res

if __name__ == "__main__":
    db = DB()
    db.initialize_tables()
    id = db.add_game("Boston Celtics", "Miami Heat", 104, 94, "2023-09-12")
    print(f"game id: {id}")
    print(db.get_games())
    db.close()
