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
                database="postgres",
                host="localhost",
                user="postgres",
                password="password",
                port="5432"
            )
            logger.info("DB connection successful")
        except Exception as e:
            logger.error(e)
        return conn

    def get_games(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * from games;")
        res = cursor.fetchall()
        return res

if __name__ == "__main__":
    db = DB()
    print(db.get_games())
