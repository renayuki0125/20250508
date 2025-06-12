# models.py
from flask_login import UserMixin
import sqlite3

class User(UserMixin):
    def __init__(self, id, staff_id, name, password_hash, is_admin):
        self.id = id
        self.staff_id = staff_id
        self.name = name
        self.password_hash = password_hash
        self._is_admin = is_admin

    @property
    def is_admin(self):
        return self._is_admin == 1

    @staticmethod
    def get(user_id):
        conn = sqlite3.connect("todo.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return User(row["id"], row["staff_id"], row["name"], row["password_hash"], row["is_admin"])
        return None
