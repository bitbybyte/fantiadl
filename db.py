import time
import sqlite3

class FantiaDlDatabase:
    def __init__(self, db_path):
        if db_path is None:
            self.conn = None
            return

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS urls (url TEXT PRIMARY KEY, timestamp INTEGER)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, title TEXT, fanclub INTEGER, posted_at INTEGER, converted_at INTEGER, download_complete INTEGER, timestamp INTEGER)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS post_contents (id INTEGER PRIMARY KEY, parent_post INTEGER, title TEXT, category TEXT, price INTEGER, currency TEXT, timestamp INTEGER, FOREIGN KEY(parent_post) REFERENCES posts(id))")

        self.conn.commit()

    def __del__(self):
        if self.conn is not None:
            self.conn.close()

    # Helper methods

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

    # INSERT, REPLACE

    def insert_post(self, id, title, fanclub, posted_at, converted_at):
        self.execute("REPLACE INTO posts VALUES (?, ?, ?, ?, ?, 0, ?)", (id, title, fanclub, posted_at, converted_at, int(time.time())))

    def insert_post_content(self, id, parent_post, title, category, price, price_unit):
        self.execute("INSERT INTO post_contents VALUES (?, ?, ?, ?, ?, ?, ?)", (id, parent_post, title, category, price, price_unit, int(time.time())))

    def insert_url(self, url):
        self.execute("INSERT INTO urls VALUES (?, ?)", (url, int(time.time())))

    # SELECT

    def find_post(self, id):
        return self.fetchone("SELECT * FROM posts WHERE id = ?", (id,))

    def is_post_content_downloaded(self, id):
        return self.fetchone("SELECT timestamp FROM post_contents WHERE id = ?", (id,)) is not None

    def is_url_downloaded(self, url):
        return self.fetchone("SELECT timestamp FROM urls WHERE url = ?", (url,)) is not None

    # UPDATE

    def update_post_download_complete(self, id, download_complete=1):
        self.execute("UPDATE posts SET download_complete = ?, timestamp = ? WHERE id = ?", (download_complete, int(time.time()), id))

    def update_post_converted_at(self, id, converted_at):
        self.execute("UPDATE posts SET converted_at = ?, timestamp = ? WHERE id = ?", (converted_at, int(time.time()), id))
