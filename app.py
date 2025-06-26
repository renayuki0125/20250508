from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, LoginManager, login_user, logout_user
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from datetime import datetime
import database3
from models import User

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def get_connection_db():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    return conn


def is_admin():
    return current_user.is_authenticated and current_user.is_admin

@app.context_processor
def inject_user():
    return dict(user=current_user, name=current_user.name if current_user.is_authenticated else "")


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
    conn = get_connection_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, staff_id, name, password_hash, is_admin, approval_order, approval_level
        FROM users
        WHERE id = ?
    """, (user_id,))
    row = c.fetchone()
    conn.close()

    if row:
        return User(
            id=row["id"],
            staff_id=row["staff_id"],
            name=row["name"],
            password_hash=row["password_hash"],
            is_admin=bool(row["is_admin"]),
            approval_level=row["approval_level"],
            approval_order=row["approval_order"]
        )
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        staff_id = request.form.get('staff_id')
        password = request.form.get('password')

        conn = get_connection_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE staff_id = ?", (staff_id,))
        row = c.fetchone()
        conn.close()

        if row and check_password_hash(row['password_hash'], password):
            user = User(row['id'], row['staff_id'], row['name'], row['password_hash'], row['is_admin'])
            login_user(user)
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
        approval_level = int(request.form["approval_level"])
        approval_order = int(request.form["approval_order"])
        role_level = int(request.form["role_level"])
        is_admin_flag = int(request.form.get("is_admin", 0))  # ← 1が送られてくる想定
        role_level = int(request.form["role_level"])
        is_admin_flag = 1 if role_level == 9 else 0


                
        try:
            conn = get_connection_db()
            c = conn.cursor()
            c.execute("""
                 INSERT INTO users (staff_id, name, password_hash, is_admin, approval_level, approval_order, role_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (staff_id, name, hashed_password, current_user.is_admin, is_admin_flag, approval_level, approval_order, role_level))
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
@login_required
def index():
    if request.method == "POST":
        machine_no = request.form["machine_no"]
        date = request.form["date"]
        shift = request.form["shift"]
        operator = current_user.name
        product_no = request.form["product_no"]
        note = request.form["note"]
        updater = current_user.name

        # 以下、追加の値を定義
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_at = created_at
        additional_note = ""
        resolved = 0
        status = "no_issue" if "問題なし" in note else "has_issue"
        resolved_by = ""

        # 13個の値を渡す
        database3.add_work_note(
            machine_no, date, shift, operator, product_no, note,
            created_at, updated_at, additional_note, updater,
            resolved, status, resolved_by
        )

        return redirect(url_for("index"))
    else:
        machine_no = request.args.get("machine_no")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        resolved_str = request.args.get("resolved")
        resolved = int(resolved_str) if resolved_str in ["0", "1"] else None
        work_notes = database3.get_filtered_work_notes(machine_no, start_date, end_date, resolved)
        machine_nos = database3.get_machine_nos()
        notes = database3.get_work_notes_with_approvals(machine_no, start_date, end_date, resolved)
        return render_template("index.html", work_notes=work_notes, machine_nos=machine_nos, name=current_user.name, user=current_user, notes=notes)
    



# @app.route("/show/<int:id>")
# @login_required
# # def show(id):
# #     note = database3.show_work_note(id)
# #     histories = database3.get_note_history(id)
# #     return render_template("show.html", note=note, histories=histories, name=current_user.name, user=current_user)

# def show(id):
#     note = database3.show_work_note(id)
#     histories = database3.get_note_history(id)
#     approvals = database3.get_approvals_by_note_id(id)  # 各approval_levelを取得する想定
#     return render_template("show.html", note=note, histories=histories, approvals=approvals, user=current_user)



@app.route("/show/<int:id>")
@login_required
def show(id):
    note = database3.show_work_note(id)
    histories = database3.get_note_history(id)
    approvals = database3.get_approval_details(note_id=id)  # ← 新しい関数を呼ぶ
    return render_template("show.html", note=note, histories=histories, approvals=approvals, user=current_user)



@app.route("/update/<int:id>", methods=["POST"])
@login_required
def update_note(id):
    additional_note = request.form["additional_note"]
    updater = current_user.name
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection_db()
    c = conn.cursor()
    c.execute("SELECT note FROM work_notes WHERE id = ?", (id,))
    original_note = c.fetchone()["note"]

    new_note = f"{original_note}\n---\n【追記者】{updater}（{now}）\n{additional_note}"
    new_status = "resolved"

    c.execute("""
        UPDATE work_notes
        SET note = ?, updated_at = ?, updater = ?, status = ?
        WHERE id = ?
    """, (new_note, now, updater, new_status, id))

    c.execute("""
        INSERT INTO note_histories (note_id, note_text, updated_at, updated_by)
        VALUES (?, ?, ?, ?)
    """, (id, new_note, now, updater))

    conn.commit()
    conn.close()
    return redirect(url_for("show", id=id))


@app.route("/resolve_note/<int:id>", methods=["POST"])
@login_required
def resolve_note(id):
    updater = current_user.name
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection_db()
    c = conn.cursor()
    c.execute("""
        UPDATE work_notes
        SET resolved = 1,
            resolved_by = ?,
            updated_at = ?,
            updater = ?,
            status = 'resolved'
        WHERE id = ?
    """, (updater, now, updater, id))

    conn.commit()
    conn.close()
    flash("処置済みにしました", "success")
    return redirect(url_for("show", id=id))


@app.route("/logout")
@login_required
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
    c.execute("SELECT id, staff_id, name, is_admin, role_level FROM users")
    users = c.fetchall()
    conn.close()
    return render_template("admin_users.html", users=users, name=current_user.name, user=current_user)


@app.route('/admin/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
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
        password = request.form.get('password')
        is_admin_flag = int(request.form.get('is_admin', 0))
        hashed_password = generate_password_hash(password)
        role_level = int(request.form["role_level"])  # ← 役職の数値を受け取る
        approval_order = int(request.form.get('approval_order', 0))
        role_level = int(request.form["role_level"])
        is_admin_flag = 1 if role_level == 9 else 0


        try:
            conn = get_connection_db()
            c = conn.cursor()
            
            c.execute("""
                INSERT INTO users (staff_id, name, password_hash, is_admin, approval_order, role_level)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (staff_id, name, hashed_password, is_admin_flag, approval_order, role_level))
            conn.commit()
            conn.close()
            flash("ユーザーを登録しました")
            return redirect(url_for('admin_users'))
        except sqlite3.IntegrityError:
            flash("社員番号がすでに存在します")
            return redirect(url_for('admin_register'))

    return render_template("admin_register.html", name=current_user.name, user=current_user)


@app.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    conn = get_connection_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, staff_id, name, is_admin, approval_level, approval_order, role_level
        FROM users WHERE id = ?
    """, (user_id,))

    user = c.fetchone()

    if not user:
        flash("ユーザーが見つかりません。")
        return redirect(url_for('admin_users'))

    if request.method == 'POST':
        name = request.form['name']
        is_admin_flag = int(request.form.get('is_admin', 0))
        password = request.form.get("password")  # ← 入力がない場合 None
        approval_level = int(request.form.get('approval_level', 1))
        approval_order = int(request.form.get('approval_order', 1))
        # role_level = int(request.form.get('role_level', 1))
        role_level = int(request.form["role_level"])
        is_admin_flag = 1 if role_level == 9 else 0



         # 管理者なら approval_order を強制的に5に
        if role_level == 9:
            approval_order = 5
        else:
            approval_order = int(request.form["approval_order"])
            
        if password:
            hashed_password = generate_password_hash(password)
            c.execute("""
                UPDATE users
                SET name = ?, is_admin = ?, password_hash = ?, role_level = ?, approval_level = ?, approval_order = ?
                WHERE id = ?
            """, (name, is_admin_flag, hashed_password, role_level, approval_level, approval_order, user_id))
        else:
            c.execute("""
                UPDATE users
                SET name = ?, is_admin = ?, role_level = ?, approval_level = ?, approval_order = ?
                WHERE id = ?
            """, (name, is_admin_flag, role_level, approval_level, approval_order, user_id))

        conn.commit()
        conn.close()
        flash("ユーザー情報を更新しました。")
        return redirect(url_for('admin_users'))

    conn.close()
    return render_template('admin_edit_user.html', user=user, name=current_user.name)



@app.route('/mark_checked/<int:id>')
@login_required
@admin_required
def mark_checked(id):
    conn = get_connection_db()
    c = conn.cursor()
    c.execute("UPDATE work_reports SET status = '確認済み', updated_by = ?, updated_at = datetime('now') WHERE id = ?", 
              (current_user.name, id))
    conn.commit()
    conn.close()
    flash("申し送りを確認済みにしました。")
    return redirect(url_for('index'))  # 一覧ページに戻す



@app.route('/mark_completed/<int:id>')
@login_required
@admin_required
def mark_completed(id):
    conn = get_connection_db()
    c = conn.cursor()
    c.execute("UPDATE work_reports SET status = '完了', updated_by = ?, updated_at = datetime('now') WHERE id = ?", 
              (current_user.name, id))
    conn.commit()
    conn.close()
    flash("申し送りを完了にしました。")
    return redirect(url_for('index'))


@app.route('/approve/<int:note_id>', methods=['POST'])
@login_required
@admin_required
def approve_note(note_id):
    user_id = current_user.id
    comment = request.form.get("comment", "")
    approval_order = current_user.approval_order
    approval_level = current_user.approval_level
    approved_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # ←追加！
    print("DEBUG: order:", approval_order, "| level:", approval_level)

    if approval_order is None or approval_level is None:
        flash("承認権限が正しく設定されていません（approval_order, approval_level）")
        return redirect(url_for("index"))
    
    conn = get_connection_db()
    c = conn.cursor()

    

    # すでに承認済みかチェック
    c.execute("""
        SELECT 1 FROM approvals
        WHERE work_note_id = ? AND approver_id = ?
    """, (note_id, user_id))
    if c.fetchone():
        flash("すでに承認済みです")
        conn.close()
        return redirect(url_for('index'))

    # 承認記録を追加
    c.execute("""
        INSERT INTO approvals (work_note_id, approver_id, approval_order, approval_level, approved_at, comment)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (note_id, user_id, approval_order, approval_level, approved_at, comment))

    # 工場長が承認 → ロック
    if approval_level == 5:
        c.execute("UPDATE work_notes SET is_locked = 1 WHERE id = ?", (note_id,))

    conn.commit()
    conn.close()

    flash("承認しました")
    return redirect(url_for('index'))






if __name__ == "__main__":
    app.run(port=8000, debug=True)
