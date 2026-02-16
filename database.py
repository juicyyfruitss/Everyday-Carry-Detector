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
        # Items table
        itemTableExist = self.cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='items';")
        if not itemTableExist.fetchone():
            self.cur.execute("""
               CREATE TABLE items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            mac TEXT
                 )
         """)

        self.conn.commit()

    def add_item(self, name, desc, mac):
        self.cur.execute(
            "INSERT INTO items (name, description, mac) VALUES (?, ?, ?)",
            (name, desc, mac)
        )
        self.conn.commit()

    def update_item(self, item_id, name, desc, mac):
        self.cur.execute(
            "UPDATE items SET name=?, description=?, mac=? WHERE id=?",
            (name, desc, mac, item_id)
        )
        self.conn.commit()

    def delete_item(self, item_id):
        self.cur.execute("DELETE FROM items WHERE id=?", (item_id,))
        self.conn.commit()

    def get_items(self):
        self.cur.execute("SELECT id, name, description, mac FROM items")
        return self.cur.fetchall()

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

    def GetCurrentUser(self):
        """
        returning the currently used email address
        """

        return self.current_user  # this must be the email string
    # class DBHandler(logging.Handler):
    #     def __init__(self):
    #         super().__init__()

    #     def emit(self, record):
    #         when = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
    #         label = log.LevelLabels.get(record.levelname, record.levelname.title())
    #         message = record.getMessage()
    #         self.LogEvent(label, message, when)
