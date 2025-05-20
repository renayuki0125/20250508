from flask import Flask, render_template, request, redirect, url_for
from database import get_work_notes, add_work_note, show_work_note, get_filtered_work_notes, get_machine_nos, get_connection_db, get_note_history
from datetime import datetime


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # 新規追加処理（今のままでOK）
        machine_no = request.form["machine_no"]
        date = request.form["date"]
        shift = request.form["shift"]
        operator = request.form["operator"]
        product_no = request.form["product_no"]
        note = request.form["note"]
        add_work_note(machine_no, date, shift, operator, product_no, note)
        return redirect(url_for("index"))

    else:
        # ✅ 絞り込み処理に変更
        machine_no = request.args.get("machine_no")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        work_notes = get_filtered_work_notes(machine_no, start_date, end_date)
        machine_nos = get_machine_nos()  # ← 機械№一覧

        return render_template("index.html", work_notes=work_notes)


@app.route("/show/<int:id>")
def show(id):
    note = show_work_note(id)
    histories = get_note_history(id)  # ✅ 履歴も取得
    return render_template("show.html", note=note, histories=histories)


@app.route("/update/<int:id>", methods=["POST"])
def update_note(id):
    additional_note = request.form["additional_note"]

    updater = request.form["updater"]  # フォームから追記者を受け取る

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection_db()
    c = conn.cursor()

    # もとの note を取得
    c.execute("SELECT note FROM work_notes WHERE id = ?", (id,))
    original_note = c.fetchone()["note"]

    # 追記（前の内容 + 改行 + 追記内容）
    new_note = f"{original_note}\n---\n【追記者】{updater}（{now}）\n{additional_note}"

    # # 上書きではなく結合して保存
    # c.execute("""
    #     UPDATE work_notes
    #     SET note = ?, updated_at = ?
    #     WHERE id = ?
    # """, (new_note, now, id))
     # work_notes を更新
    c.execute("""
        UPDATE work_notes
        SET note = ?, updated_at = ?, updater = ?
        WHERE id = ?
    """, (new_note, now, updater, id))

    # ✅ 履歴テーブルにも保存
    c.execute("""
        INSERT INTO note_histories (note_id, note_text, updated_at, updated_by)
        VALUES (?, ?, ?, ?)
    """, (id, new_note, now, updater))

    conn.commit()
    conn.close()

    return redirect(url_for("show", id=id))

if __name__ == "__main__":
    app.run(port=8000, debug=True)


    
