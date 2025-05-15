# import sqlite3


# # データベース接続する関数
# def get_connection_db():
#     conn = sqlite3.connect("todo.db")
#     # 行を辞書として取得
#     conn.row_factory = sqlite3.Row
#     return conn


# # テーブルを作成
# def create_table():
#     conn = get_connection_db()
#     c = conn.cursor()
#     c.execute(
#         """
#         CREATE TABLE IF NOT EXISTS work_notes (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         machine_no TEXT NOT NULL,           -- 機械番号
#         date DATE NOT NULL,                 -- 日付
#         shift TEXT NOT NULL,                -- 勤務帯（例：早番、遅番など）
#         operator TEXT NOT NULL,             -- 担当者
#         product_no TEXT NOT NULL,           -- 品番
#         note TEXT NOT NULL,                 -- 申し送り内容
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#     )
# """
#     )


# create_table()


import sqlite3


# データベース接続関数
def get_connection():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    return conn


# 作業申し送り一覧を取得
def get_work_notes():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM work_notes ORDER BY date DESC, id DESC")
    rows = c.fetchall()
    conn.close()
    return rows


# 作業申し送りを1件追加
def add_work_note(machine_no, date, shift, operator, product_no, note):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO work_notes (machine_no, date, shift, operator, product_no, note)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (machine_no, date, shift, operator, product_no, note),
    )
    conn.commit()
    conn.close()


# IDで1件取得（詳細表示用）
def show_work_note(note_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM work_notes WHERE id = ?", (note_id,))
    row = c.fetchone()
    conn.close()
    return row


def get_filtered_work_notes(machine_no=None, start_date=None, end_date=None):
    conn = get_connection()
    c = conn.cursor()
    query = "SELECT * FROM work_notes WHERE 1=1"
    params = []

    if machine_no:
        query += " AND machine_no LIKE ?"
        params.append(f"%{machine_no}%")

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC, id DESC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows


# def get_machine_nos():
#     conn = get_connection_db()
#     c = conn.cursor()
#     c.execute("SELECT DISTINCT machine_no FROM work_notes ORDER BY machine_no")
#     return [row["machine_no"] for row in c.fetchall()]
