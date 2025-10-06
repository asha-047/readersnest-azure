from flask import Flask, request, render_template, redirect, session, send_from_directory
import pymysql
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
# Use an environment variable for the secret key for better security
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-super-secret-key')
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# This line is important: It ensures the 'uploads' folder gets created inside the container
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    """
    Creates a new database connection for Azure Database for MySQL.
    It uses environment variables for credentials and requires an SSL certificate.
    """
    return pymysql.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        db=os.environ.get('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor,
        # This line is critical for a secure connection to Azure
        ssl_ca='DigiCertGlobalRootG2.crt.pem'
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Using a try-except block is good practice for database operations
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # In a real app, you should hash passwords for security
                cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
                conn.commit()
            conn.close()
            return redirect('/login')
        except pymysql.err.IntegrityError:
            return render_template('register.html', error="Username already exists.")
        except Exception as e:
            # This helps in debugging if other database errors occur
            print(f"An error occurred: {e}")
            return "An internal server error occurred", 500
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
    # This part is for local development and won't be used by Gunicorn in Azure
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
