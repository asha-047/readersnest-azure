from flask import Flask, request, render_template, redirect, session, send_from_directory
import pymysql
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    return pymysql.connect(
        unix_socket=os.environ['DB_HOST'],
        user='libadmin',
        password='libadmin',
        db='lib',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
                conn.commit()
            return redirect('/login')
        except pymysql.err.IntegrityError:
            return render_template('register.html', error="Username already exists.")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
            user = cursor.fetchone()
        conn.close()
        if user:
            session['user'] = user['username']
            return redirect('/')
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
    conn.close()
    return render_template('index.html', books=books)

@app.route('/search')
def search():
    if 'user' not in session:
        return redirect('/login')
    query = request.args.get('q', '')
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM books WHERE title LIKE %s OR author LIKE %s", (f"%{query}%", f"%{query}%"))
        books = cursor.fetchall()
    conn.close()
    return render_template('index.html', books=books, query=query)

@app.route('/add', methods=['POST'])
def add():
    if 'user' not in session:
        return redirect('/login')
    title = request.form['title']
    author = request.form['author']
    file = request.files.get('file')
    filename = None
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO books (title, author, filename) VALUES (%s, %s, %s)", (title, author, filename))
        conn.commit()
    conn.close()
    return redirect('/')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user' not in session:
        return redirect('/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        file = request.files.get('file')
        filename = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cursor.execute("UPDATE books SET title=%s, author=%s, filename=%s WHERE id=%s", (title, author, filename, id))
        else:
            cursor.execute("UPDATE books SET title=%s, author=%s WHERE id=%s", (title, author, id))
        conn.commit()
        conn.close()
        return redirect('/')
    cursor.execute("SELECT * FROM books WHERE id=%s", (id,))
    book = cursor.fetchone()
    conn.close()
    return render_template('edit.html', book=book)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
