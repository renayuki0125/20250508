from flask import Flask, render_template, request, redirect, url_for
from database import get_work_notes, add_work_note, show_work_note, get_filtered_work_notes, get_machine_nos

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
    return render_template("show.html", note=note)


if __name__ == "__main__":
    app.run(port=8000, debug=True)
