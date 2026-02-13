import sqlite3
import logging
import log
from datetime import datetime, timedelta


class DB:
    def __init__(self):
        self.conn = sqlite3.connect('Log.db')
        self.cur = self.conn.cursor()
        self.create_table()

    def create_table(self):
        # Events table
        tableExist = self.cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='events';")
        if not tableExist.fetchone():
            self.cur.execute(
                "CREATE TABLE events (level TEXT, event TEXT, timestamp TEXT)")

        # Users table
        userTableExist = self.cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not userTableExist.fetchone():
            self.cur.execute(
                "CREATE TABLE users (username TEXT PRIMARY KEY, password TEXT)")

        self.conn.commit()

    def LogEvent(self, level, event, timestamp):
        self.cur.execute(
            f"INSERT INTO events (level, event, timestamp) VALUES ('{level}', '{event}', '{timestamp}')")
        self.conn.commit()

# gets all events from the database that are not older then 14 days old
    def GetEvents(self):
        self.cur.execute(
            f"SELECT * FROM events WHERE timestamp >= '{(datetime.now() + timedelta(days=-14)).strftime('%Y-%m-%d %H:%M:%S')}'")
        return self.cur.fetchall()

    def create_user(self, username, password):
        try:
            # In a real app, hash password here!
            self.cur.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username, password):
        self.cur.execute(
            "SELECT password FROM users WHERE username = ?", (username,))
        result = self.cur.fetchone()
        if result and result[0] == password:
            return True
        return False

    # class DBHandler(logging.Handler):
    #     def __init__(self):
    #         super().__init__()

    #     def emit(self, record):
    #         when = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
    #         label = log.LevelLabels.get(record.levelname, record.levelname.title())
    #         message = record.getMessage()
    #         self.LogEvent(label, message, when)
