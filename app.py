from flask import Flask, request, render_template, redirect, session, send_from_directory
import pymysql
from werkzeug.utils import secure_filename
import os
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-super-secret-key')

# --- START OF BLOB STORAGE CONFIG ---
# We no longer need the local UPLOAD_FOLDER
CONTAINER_NAME = "books"
CONNECT_STR = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
# Create a BlobServiceClient to interact with the storage account
blob_service_client = BlobServiceClient.from_connection_string(CONNECT_STR)
# --- END OF BLOB STORAGE CONFIG ---


def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        db=os.environ.get('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor,
        ssl_ca='DigiCertGlobalRootG2.crt.pem'
    )

# --- ROUTES (Login, Register, Logout are unchanged) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
                conn.commit()
            conn.close()
            return redirect('/login')
        except pymysql.err.IntegrityError:
            return render_template('register.html', error="Username already exists.")
        except Exception as e:
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

# --- START OF MODIFIED UPLOAD/DOWNLOAD LOGIC ---
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
        # Upload the file to Azure Blob Storage instead of saving locally
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=filename)
        blob_client.upload_blob(file.read(), overwrite=True)

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO books (title, author, filename) VALUES (%s, %s, %s)", (title, author, filename))
        conn.commit()
    conn.close()
    return redirect('/')

# Edit function is similar, but not included here for brevity

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if 'user' not in session:
        return redirect('/login')
    
    # Get a blob client to interact with the specific blob
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=filename)

    # Generate a SAS token that is valid for 1 hour
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=CONTAINER_NAME,
        blob_name=filename,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )

    # Create the full URL for the blob with the SAS token
    blob_url_with_sas = f"{blob_client.url}?{sas_token}"
    
    # Redirect the user's browser to the secure, temporary download link
    return redirect(blob_url_with_sas)

# --- END OF MODIFIED UPLOAD/DOWNLOAD LOGIC ---

# Edit function - also updated for blob storage
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
            # Upload the new file to Azure Blob Storage
            blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=filename)
            blob_client.upload_blob(file.read(), overwrite=True)
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

