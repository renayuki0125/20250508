import sqlite3
from datetime import datetime

def get_connection_db():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    print("ok")
    return conn


get_connection_db()

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
def add_work_note(machine_no, date, shift, operator, product_no, note,
                  created_at, updated_at, additional_note, updater,
                  resolved, status, resolved_by):

    conn = get_connection_db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO work_notes (
            machine_no, date, shift, operator,
            product_no, note, created_at, updated_at,
            additional_note, updater, resolved, status, resolved_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (machine_no, date, shift, operator,
          product_no, note, created_at, updated_at,
          additional_note, updater, resolved, status, resolved_by))

    conn.commit()
    conn.close()


def show_work_note(note_id):
    conn = get_connection_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, machine_no, date, shift, operator, product_no, note, updater, updated_at, resolved
        FROM work_notes
        WHERE id = ?
    """, (note_id,)
    )
    row = c.fetchone()
    conn.close()
    return row





def approve_by_a(note_id, approver_name):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection_db()
    c = conn.cursor()
    c.execute("""
        UPDATE work_notes
        SET approved_by_a = ?, approved_at_a = ?, approval_status = 'A承認済み'
        WHERE id = ?
    """, (approver_name, now, note_id))
    conn.commit()
    conn.close()


def get_work_notes_with_approvals(machine_no=None, start_date=None, end_date=None, resolved=None):
    conn = get_connection_db()
    c = conn.cursor()

    query = "SELECT * FROM work_notes WHERE 1=1"
    params = []

    if machine_no not in [None, ""]:
        query += " AND machine_no = ?"
        params.append(machine_no)

    if start_date not in [None, ""]:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date not in [None, ""]:
        query += " AND date <= ?"
        params.append(end_date)

    if resolved in [0, 1]:  # resolved は int 型になる前提
        query += " AND resolved = ?"
        params.append(resolved)

    query += " ORDER BY date DESC"
    c.execute(query, params)
    rows = c.fetchall()

    notes = []
    for row in rows:
        note = dict(row)  # ← dict化して扱いやすく
        # 承認者IDを取得
        c.execute("SELECT approver_id FROM approvals WHERE work_note_id = ?", (note['id'],))
        note['approved_user_ids'] = [r['approver_id'] for r in c.fetchall()]
        note['is_locked'] = len(note['approved_user_ids']) >= 5
        notes.append(note)

    conn.close()
    return notes



def get_approvals_by_note_id(note_id):
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT approval_level FROM approvals WHERE work_note_id = ?
    """, (note_id,))
    approvals = c.fetchall()
    conn.close()
    return approvals

def get_approval_details(note_id):
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT a.approval_order, a.approval_level, a.approved_at, a.comment,
               u.name
        FROM approvals a
        JOIN users u ON a.approver_id = u.id
        WHERE a.work_note_id = ?
        ORDER BY a.approval_order ASC
    """, (note_id,))
    results = c.fetchall()
    conn.close()
    return results

