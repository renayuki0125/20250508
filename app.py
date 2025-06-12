from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user, LoginManager, login_user, logout_user
import sqlite3
from werkzeug.security import check_password_hash
import database3
from datetime import datetime
from werkzeug.security import generate_password_hash
from functools import wraps
from models import User          # ← ここを書き換え



app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # セキュリティのため適当なランダム文字列を設定


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'




def get_connection_db():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    return conn

def is_admin():
    return session.get('is_admin') == 1

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("管理者のみアクセスできます。")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        password = request.form['password']

        conn = get_connection_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE staff_id = ?", (staff_id,))
        row = c.fetchone()
        conn.close()

        if row and check_password_hash(row['password_hash'], password):
            user = User(row['id'], row['staff_id'], row['name'], row['password_hash'], row['is_admin'])
            login_user(user)
            # flash("ログインしました。")
            return redirect(url_for('index'))
        else:
            flash("社員番号またはパスワードが間違っています。")
            return redirect(url_for('login'))

    return render_template("login.html")

    
@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if not is_admin():
        flash("この機能にアクセスできません。")
        return redirect(url_for("login"))


    if request.method == "POST":
        staff_id = request.form["staff_id"]
        name = request.form["user_name"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)
        try:
            conn = get_connection_db()
            c = conn.cursor()
            c.execute("""
                INSERT INTO users (staff_id, name, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
            """, (staff_id, name, hashed_password, is_admin))
            conn.commit()
            conn.close()
            flash("登録が完了しました。")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("この社員番号はすでに登録されています。")
            return redirect(url_for("register"))
    else:
        return render_template("register.html")
@app.route("/", methods=["GET", "POST"])
def index():
    # ✅ ログインしていない場合はログイン画面へリダイレクト
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        # 新規追加処理（今のままでOK）
        machine_no = request.form["machine_no"]
        date = request.form["date"]
        shift = request.form["shift"]
        operator = session.get("user_name")  # ログイン中のユーザー名を担当者として記録
        product_no = request.form["product_no"]
        note = request.form["note"]
        updater = session.get("user_name")
        database3.add_work_note(machine_no, date, shift, operator, product_no, note, updater)
        return redirect(url_for("index"))
    else:
        # ✅ 絞り込み処理に変更
        machine_no = request.args.get("machine_no")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        resolved_str = request.args.get("resolved")
        resolved = int(resolved_str) if resolved_str in ["0", "1"] else None
        work_notes = database3.get_filtered_work_notes(machine_no, start_date, end_date, resolved)
        machine_nos = database3.get_machine_nos()  # ← 機械№一覧

        # return render_template("index.html", work_notes=work_notes)
        
        return render_template("index.html", work_notes=work_notes, machine_nos=machine_nos, name=session['user_name'])



@app.route("/show/<int:id>")
def show(id):
    # ✅ ログインしていない場合はログイン画面へリダイレクト
    if "user_id" not in session:
        return redirect(url_for("login"))
    else:
        note = database3.show_work_note(id)
        histories = database3.get_note_history(id)  # ✅ 履歴も取得
        return render_template("show.html", note=note, histories=histories)

@app.route("/update/<int:id>", methods=["POST"])
def update_note(id):
    # ✅ ログインしていない場合はログイン画面へリダイレクト
    if "user_id" not in session:
        return redirect(url_for("login"))
    else:
        additional_note = request.form["additional_note"]
        updater = session.get("user_name")  # ログインユーザー名を自動で取得
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection_db()
        c = conn.cursor()

        # 元の note を取得
        c.execute("SELECT note FROM work_notes WHERE id = ?", (id,))
        original_note = c.fetchone()["note"]

        # note を追記
        new_note = f"{original_note}\n---\n【追記者】{updater}（{now}）\n{additional_note}"

        # 状況に応じて status を変更（例: 対応済）
        new_status = "resolved"

        # note本体の更新
        c.execute(
            """
            UPDATE work_notes
            SET note = ?, updated_at = ?, updater = ?, status = ?
            WHERE id = ?
        """,
            (new_note, now, updater, new_status, id),
        )

        # 履歴にも保存
        c.execute(
            """
            INSERT INTO note_histories (note_id, note_text, updated_at, updated_by)
            VALUES (?, ?, ?, ?)
        """,
            (id, new_note, now, updater),
        )

        conn.commit()
        conn.close()

        return redirect(url_for("show", id=id))


@app.route("/resolve_note/<int:id>", methods=["POST"])
def resolve_note(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    updater = session.get("user_name")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(updater, now, updater, id)
    conn = get_connection_db()
    c = conn.cursor()

    # 処置済みに変更、更新者と時刻を保存
    c.execute("""
        UPDATE work_notes
        SET resolved = 1,
            resolved_by = ?,
            updated_at = ?,
            updater = ?,
            status = 'resolved'
        WHERE id = ?
    """, (updater, now, updater, id,))

    conn.commit()
    conn.close()

    flash("処置済みにしました", "success")
    return redirect(url_for("show", id=id))



@app.route("/logout")
def logout():
    logout_user()
    flash("ログアウトしました。")
    return redirect(url_for("login"))



@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    conn = get_connection_db()
    c = conn.cursor()
    c.execute("SELECT id, staff_id, name, is_admin FROM users")
    users = c.fetchall()
    conn.close()
    return render_template("admin_users.html", users=users)

@app.route('/admin/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = get_connection_db()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("ユーザーを削除しました")
    return redirect(url_for('admin_users'))


@app.route('/admin/register', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_register():
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        name = request.form['name']
        password = request.form['password']
        is_admin_flag = int(request.form.get('is_admin', 0))
        hashed_password = generate_password_hash(password)

        try:
            conn = get_connection_db()
            c = conn.cursor()
            c.execute("""
                INSERT INTO users (staff_id, name, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
            """, (staff_id, name, hashed_password, is_admin_flag))
            conn.commit()
            conn.close()
            flash("ユーザーを登録しました")
            return redirect(url_for('admin_users'))
        except sqlite3.IntegrityError:
            flash("社員番号がすでに存在します")
            return redirect(url_for('admin_register'))

    return render_template("admin_register.html")


@app.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    conn = get_connection_db()
    c = conn.cursor()

    # ユーザー情報取得
    c.execute("SELECT id, staff_id, name, is_admin FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()

    if not user:
        flash("ユーザーが見つかりません。")
        return redirect(url_for('admin_users'))

    if request.method == 'POST':
        name = request.form['name']
        is_admin_flag = int(request.form.get('is_admin', 0))
        password = request.form['password']

        # パスワードが入力されていればハッシュ化して更新
        if password:
            hashed_password = generate_password_hash(password)
            c.execute("""
                UPDATE users
                SET name = ?, is_admin = ?, password_hash = ?
                WHERE id = ?
            """, (name, is_admin_flag, hashed_password, user_id))
        else:
            c.execute("""
                UPDATE users
                SET name = ?, is_admin = ?
                WHERE id = ?
            """, (name, is_admin_flag, user_id))

        conn.commit()
        conn.close()

        flash("ユーザー情報を更新しました。")
        return redirect(url_for('admin_users'))

    conn.close()
    return render_template('admin_edit_user.html', user=user)



if __name__ == "__main__":
    app.run(port=8000, debug=True)