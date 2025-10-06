# Readers' Nest

---

# 📚 Readers' Nest

**A Community-Centered Digital Library built with Flask and Google Cloud**

**Readers' Nest** is a cloud-hosted web platform where book lovers can upload, share, search, and download books. It's built as an open and collaborative reading space for everyone — whether you're a casual reader or an active contributor.

---

# 🔗 Live Demo

🌐 (https://library-app-545075885582.asia-south1.run.app)

---

# ✨ Features

- 🔐 User registration & login
- 📥 Upload books with file attachments
- 🔍 Search books by title or author
- ✏️ Edit uploaded book details
- 📄 Download book files from others
- 💻 Clean, modern, responsive UI

---

# 🛠️ Tech Stack

| Layer        | Technology                       |
|--------------|----------------------------------|
| Frontend     | HTML, CSS, Bootstrap 5, Jinja2   |
| Backend      | Python (Flask)                   |
| Database     | MySQL (Cloud SQL)                |
| Hosting      | Google Cloud Run                 |
| File Storage | Flask Upload Folder              |

---

 # 📁 Folder Structure
 ```
readers-nest/
│
├── app.py # Main Flask app
├── requirements.txt # Python dependencies
├── uploads/ # Uploaded files stored here
├── templates/ # All HTML pages
│ ├── index.html
│ ├── login.html
│ ├── register.html
│ └── edit.html

````



---

# 🧠 Database Schema

users
| Field     | Type         |
|-----------|--------------|
| id        | INT (PK)     |
| username  | VARCHAR(50)  |
| password  | VARCHAR(100) |

books
| Field     | Type         |
|-----------|--------------|
| id        | INT (PK)     |
| title     | VARCHAR(100) |
| author    | VARCHAR(100) |
| filename  | VARCHAR(255) |

---

# 🚀 Deployment to Google Cloud Run

#### 1. Enable Required Services

```bash
gcloud services enable run sqladmin compute cloudbuild
```

#### 2. Build & Submit to Cloud Build

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/readers-nest
```

#### 3. Deploy to Cloud Run

```bash
gcloud run deploy readers-nest \
  --image gcr.io/YOUR_PROJECT_ID/readers-nest \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --add-cloudsql-instances YOUR_PROJECT_ID:asia-south1:lib-db \
  --set-env-vars DB_HOST=/cloudsql/YOUR_PROJECT_ID:asia-south1:lib-db
```

---

## 📦 Future Features

* 🔖 Book categories & tags
* 🌙 Dark mode
* 🧑‍💼 Admin moderation dashboard
* 🧠 AI-based book recommendations
* 📬 Email verification and recovery

---

## 👩‍💻 Author

**Asha Bhokare**

B.E. Computer Engineering

📫 [[ashabhokare74@gmail.com]]

