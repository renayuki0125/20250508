import sqlite3


def create_table():
    conn = sqlite3.connect("todo.db")  # ← あなたのDBファイル名に合わせてね
    c = conn.cursor()

    c.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id TEXT UNIQUE NOT NULL,  -- 社員番号・作業者番号
                name TEXT NOT NULL,             -- 氏名（任意）
                password_hash TEXT NOT NULL     -- ハッシュ化パスワード
        )
     """)
    
    conn.commit()
    conn.close()
if __name__ == "__main__":
    create_table()