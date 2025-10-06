from flask import Flask, request, render_template, redirect, session, send_from_directory
import pymysql
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
# It's a good practice to use a more secure, randomly generated secret key
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_default_secret_key_for_development')
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- START OF CHANGES ---

def get_db_connection():
    """
    Creates a new database connection using environment variables
    for Azure Database for MySQL.
    """
    # Azure Database for MySQL requires an SSL connection.
    # We assume the certificate file is in the root directory.
    # Azure provides this certificate, which we'll name 'DigiCertGlobalRootG2.crt.pem'
    # For local development without SSL, you can remove the 'ssl' parameter.
    return pymysql.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        db=os.environ.get('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor,
        ssl_ca='DigiCertGlobalRootG2.crt.pem'
    )

# --- END OF CHANGES ---


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # NOTE: Storing passwords in plain text is insecure.
                # In a real-world app, you should hash and salt passwords.
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

if __name__ == '__main__':
    # Use a port assigned by the environment or default to 8080
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
