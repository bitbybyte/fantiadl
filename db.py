import sqlite3

class FantiaDatabase:
    def __init__(self, db_path):
        if db_path is None:
            self.conn = None
            return

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS urls (url TEXT PRIMARY KEY, timestamp INTEGER)")

        self.conn.commit()

    def __del__(self):
        if self.conn is not None:
            self.conn.close()

    # assistant methods to compatibilize with no database mode

    def execute(self, query, args):
        if self.conn is None:
            return
        self.cursor.execute(query, args)
        self.conn.commit()

    def fetchone(self, query, args):
        if self.conn is None:
            return None
        self.cursor.execute(query, args)
        return self.cursor.fetchone()

    # insert methods

    def insert_url(self, url):
        self.execute("INSERT INTO urls VALUES (?, ?)", (url, int(time.time())))

    # select methods

    def is_url_downloaded(self, url):
        return self.fetchone("SELECT timestamp FROM urls WHERE url = ?", (url,)) is not None
