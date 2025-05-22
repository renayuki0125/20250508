import sqlite3


# データベース接続関数
def get_connection_db():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_machine_nos():
    conn = get_connection_db()
    c = conn.cursor()
    c.execute("SELECT DISTINCT machine_no FROM work_notes ORDER BY machine_no")
    return [row["machine_no"] for row in c.fetchall()]


# 作業申し送り一覧を取得
def get_work_notes():
    conn = get_connection_db()
    c = conn.cursor()
    c.execute("SELECT * FROM work_notes ORDER BY date DESC, id DESC")
    rows = c.fetchall()
    conn.close()
    return rows


# 作業申し送りを1件追加
def add_work_note(machine_no, date, shift, operator, product_no, note):
    # noteの内容から status を判定
    if "問題なし" in note:
        status = "no_issue"
    else:
        status = "has_issue"

    conn = get_connection_db()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO work_notes (machine_no, date, shift, operator, product_no, note, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (machine_no, date, shift, operator, product_no, note, status),
    )
    conn.commit()
    conn.close()


# IDで1件取得（詳細表示用）
def show_work_note(note_id):
    conn = get_connection_db()
    c = conn.cursor()
    c.execute("SELECT * FROM work_notes WHERE id = ?", (note_id,))
    row = c.fetchone()
    conn.close()
    return row


# 絞り込み取得（機械番号・日付範囲）
def get_filtered_work_notes(machine_no=None, start_date=None, end_date=None):
    conn = get_connection_db()
    c = conn.cursor()

    query = """
        SELECT id, machine_no, date, shift, operator, product_no, note, updater, updated_at
        FROM work_notes
        WHERE 1=1
    """
    params = []

    if machine_no:
        query += " AND machine_no = ?"
        params.append(machine_no)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC"

    c.execute(query, params)
    work_notes = c.fetchall()
    conn.close()
    return work_notes


# def get_note_history(note_id):
#     conn = get_connection_db()
#     c = conn.cursor()
#     c.execute("""
#         SELECT note_text, updated_at, updated_by
#         FROM note_histories
#         WHERE note_id = ?
#         ORDER BY updated_at DESC
#     """, (note_id,))
#     return c.fetchall()


def get_note_history(note_id):
    conn = get_connection_db()
    c = conn.cursor()
    c.execute(
        """
        SELECT note_text, updated_at, updated_by
        FROM note_histories
        WHERE note_id = ?
        ORDER BY updated_at DESC
    """,
        (note_id,),
    )
    histories = c.fetchall()
    conn.close()
    return histories
