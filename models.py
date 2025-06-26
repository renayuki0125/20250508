# models.py
from flask_login import UserMixin
import sqlite3

class User(UserMixin):
    def __init__(self, id, staff_id, name, password_hash, is_admin=False, approval_level=None, approval_order=None):
        self.id = id
        self.staff_id = staff_id
        self.name = name
        self.password_hash = password_hash
        self._is_admin = is_admin
        self.approval_level = approval_level
        self.approval_order = approval_order

    @property
    def is_admin(self):
        return bool(self._is_admin)
    
    def get_role_name(self):
        role_map = {
            1: '一般',
            2: '班長',
            3: '係長',
            4: '主任',
            5: '工場長',
            9: '管理者'
        }
        return role_map.get(self.role_level, '不明')

    @staticmethod
    def get(user_id):
        conn = sqlite3.connect("todo.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return User(
                    row["id"],
                    row["staff_id"],
                    row["name"],
                    row["password_hash"],
                    row["is_admin"],
                    row["approval_level"],
                    row["approval_order"],
                    row["role_level"]
                )
        return None