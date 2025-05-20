import sqlite3

def create_table():
    conn = sqlite3.connect("todo.db")  # ← あなたのDBファイル名に合わせてね
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS note_histories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id INTEGER,
            note_text TEXT,
            updated_at TEXT,
            updated_by TEXT,
            FOREIGN KEY (note_id) REFERENCES work_notes(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ note_histories テーブル作成完了！")

if __name__ == "__main__":
    create_table()