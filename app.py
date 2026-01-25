import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import pymysql
from dotenv import load_dotenv  # 환경 변수 로드를 위해 추가

# .env 파일의 내용을 환경 변수로 불러옴
load_dotenv()

app = Flask(__name__)
# 환경 변수에서 가져오되, 없으면 기본값을 사용
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# --- [파일 업로드 설정] ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_db():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'), 
        db=os.getenv('DB_NAME'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def index():
    return redirect(url_for('login'))

# --- 로그인 / 회원가입 / 아이디-비번 찾기 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('id')
        user_pw = request.form.get('pw')
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE id=%s AND pw=%s", (user_id, user_pw))
            user = cur.fetchone()
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('posts_list'))
        flash("로그인 정보가 일치하지 않습니다.")
    return render_template('login.html')

@app.route('/check_id', methods=['POST'])
def check_id():
    user_id = request.json.get('id')
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
    if user:
        return jsonify({"result": "fail", "message": "이미 사용 중인 아이디입니다."})
    return jsonify({"result": "success", "message": "사용 가능한 아이디입니다."})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form.get('id')
        user_pw = request.form.get('pw')
        user_name = request.form.get('name')
        user_gender = request.form.get('gender')
        user_birth = request.form.get('birthdate')
        user_school = request.form.get('school')
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE id=%s", (user_id,))
            if cur.fetchone(): return "이미 존재하는 아이디입니다.", 400
            sql = "INSERT INTO users (id, pw, name, gender, birthdate, school) VALUES (%s, %s, %s, %s, %s, %s)"
            cur.execute(sql, (user_id, user_pw, user_name, user_gender, user_birth, user_school))
        db.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/find_id', methods=['GET', 'POST'])
def find_id():
    if request.method == 'POST':
        name = request.form.get('name'); birth = request.form.get('birthdate'); school = request.form.get('school')
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE name=%s AND birthdate=%s AND school=%s", (name, birth, school))
            user = cur.fetchone()
        if user: flash(f"아이디는 [{user['id']}] 입니다."); return redirect(url_for('login'))
        flash("정보가 일치하지 않습니다.")
    return render_template('find_id.html')

@app.route('/find_pw', methods=['GET', 'POST'])
def find_pw():
    if request.method == 'POST':
        u_id = request.form.get('id'); name = request.form.get('name'); school = request.form.get('school')
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE id=%s AND name=%s AND school=%s", (u_id, name, school))
            user = cur.fetchone()
        if user: return render_template('reset_pw.html', user_id=u_id)
        flash("정보가 일치하지 않습니다.")
    return render_template('find_pw.html')

@app.route('/reset_pw_action', methods=['POST'])
def reset_pw_action():
    u_id = request.form.get('id'); new_pw = request.form.get('new_pw')
    db = get_db()
    with db.cursor() as cur:
        cur.execute("UPDATE users SET pw=%s WHERE id=%s", (new_pw, u_id))
    db.commit(); flash("비밀번호가 변경되었습니다."); return redirect(url_for('login'))

# --- [프로필 관련 기능] ---
@app.route('/profile/<user_id>')
def profile(user_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT id, name, gender, birthdate, school, profile_img FROM users WHERE id=%s", (user_id,))
        user_info = cur.fetchone()
    if not user_info:
        flash("존재하지 않는 사용자입니다.")
        return redirect(url_for('posts_list'))
    return render_template('profile.html', user=user_info)

@app.route('/profile/edit', methods=['GET', 'POST'])
def profile_edit():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    user_id = session['user_id']
    if request.method == 'POST':
        name = request.form.get('name')
        school = request.form.get('school')
        file = request.files.get('profile_img')
        with db.cursor() as cur:
            if file and file.filename != '':
                filename = secure_filename(f"profile_{user_id}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                sql = "UPDATE users SET name=%s, school=%s, profile_img=%s WHERE id=%s"
                cur.execute(sql, (name, school, filename, user_id))
            else:
                sql = "UPDATE users SET name=%s, school=%s WHERE id=%s"
                cur.execute(sql, (name, school, user_id))
        db.commit(); flash("프로필이 수정되었습니다.")
        return redirect(url_for('profile', user_id=user_id))
    with db.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user_info = cur.fetchone()
    return render_template('profile_edit.html', user=user_info)

# --- [파일 다운로드] ---
@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# --- [게시판 목록] ---
@app.route('/posts')
def posts_list():
    if 'user_id' not in session: return redirect(url_for('login'))
    search_type = request.args.get('search_type', 'all'); keyword = request.args.get('keyword', '')
    db = get_db()
    with db.cursor() as cur:
        sql = "SELECT * FROM posts WHERE 1=1"
        params = []
        if keyword:
            if search_type == 'title': sql += " AND title LIKE %s"; params.append(f"%{keyword}%")
            elif search_type == 'content': sql += " AND content LIKE %s"; params.append(f"%{keyword}%")
            else: sql += " AND (title LIKE %s OR content LIKE %s)"; params.append(f"%{keyword}%"); params.append(f"%{keyword}%")
        sql += " ORDER BY id DESC"
        cur.execute(sql, params); posts = cur.fetchall()
    return render_template('posts_list.html', posts=posts)

# --- [새 글 작성] ---
@app.route('/post/new', methods=['GET', 'POST'])
def post_new():
    if 'user_id' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title'); content = request.form.get('content'); post_pw = request.form.get('post_pw')
        file = request.files.get('file'); filename = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db = get_db()
        with db.cursor() as cur:
            sql = "INSERT INTO posts (title, content, author, filename, post_pw) VALUES (%s, %s, %s, %s, %s)"
            cur.execute(sql, (title, content, session['user_id'], filename, post_pw))
        db.commit(); return redirect(url_for('posts_list'))
    return render_template('post_new.html')

# --- [글 상세 보기] ---
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
        post = cur.fetchone()
    if not post: return "글을 찾을 수 없습니다.", 404
    if post.get('post_pw') and post['author'] != session['user_id']:
        if request.method == 'POST':
            input_pw = request.form.get('input_pw')
            if input_pw == post['post_pw']:
                return render_template('post_detail.html', post=post)
            else:
                flash("비밀번호가 일치하지 않습니다.")
        return render_template('post_pw_check.html', post_id=post_id)
    return render_template('post_detail.html', post=post)

# --- [글 삭제] ---
@app.route('/post/<int:post_id>/delete', methods=['POST'])
def post_delete(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    with db.cursor() as cur:
        cur.execute("DELETE FROM posts WHERE id=%s AND author=%s", (post_id, session['user_id']))
    db.commit(); return redirect(url_for('posts_list'))

# --- [글 수정] ---
@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def post_edit(post_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        title = request.form.get('title'); content = request.form.get('content')
        file = request.files.get('file')
        with db.cursor() as cur:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cur.execute("UPDATE posts SET title=%s, content=%s, filename=%s WHERE id=%s AND author=%s",
                            (title, content, filename, post_id, session['user_id']))
            else:
                cur.execute("UPDATE posts SET title=%s, content=%s WHERE id=%s AND author=%s",
                            (title, content, post_id, session['user_id']))
        db.commit(); return redirect(url_for('post_detail', post_id=post_id))
    with db.cursor() as cur:
        cur.execute("SELECT * FROM posts WHERE id=%s", (post_id,))
        post = cur.fetchone()
    return render_template('post_edit.html', post=post)

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)