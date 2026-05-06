# 🎯 Smart Interview Management System

A full-stack web application built with **Flask + MongoDB + Groq AI** that streamlines the interview process — from candidate registration and resume parsing to AI-powered skill suggestions and interview preparation.

---

## ✨ Features

### 👨‍💼 Admin Side
- Secure admin login (username + password)
- View all registered candidates with their scores, skills, and interview status
- Candidates automatically scored based on resume skills
- Interview plan auto-assigned based on score

### 👤 Candidate Side
- Candidate registration with resume upload (PDF / DOCX / TXT / MD)
- Auto skill extraction from resume
- Auto score calculation (0–100)
- Auto selection status: **Selected** or **Under Review**
- Candidate login via **Email + Phone Number** (no password needed)
- Personalized candidate dashboard showing:
  - Resume score with visual progress bar
  - Detected skills
  - Interview status & plan
  - **Groq AI-powered skill improvement suggestions**
    - If **Selected** → Skills to grow for promotion in the company
    - If **Under Review** → Skills to improve to crack next interview

### 💬 Interview Preparation
- Choose subject (e.g., Python, Java, SQL)
- Choose topic (e.g., OOP, Data Structures)
- Choose level (Fresher / Intermediate / Advanced)
- Choose question type (MCQ / Theory / Coding / Mixed)
- **Groq AI generates 20 Q&As** with answers and interview tips

### 📧 Email Notification
- Automatic selection email sent to candidate when status is **Selected**

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Database | MongoDB |
| AI / LLM | Groq API (llama-3.3-70b-versatile) |
| Resume Parsing | Custom extractor (PDF/DOCX/TXT) |
| Email | SMTP (Gmail / any provider) |
| Auth | Werkzeug password hashing |

---

## 📂 Project Structure

```
smart_management_interview_system/
│
├── app.py                          # Main Flask application
│
├── app/
│   ├── templates/                  # All HTML templates
│   │   ├── base.html               # Common layout (header, nav, footer)
│   │   ├── admin_login.html        # Admin login page
│   │   ├── admin_dashboard.html    # Admin dashboard (all candidates)
│   │   ├── candidate_register.html # Candidate registration + resume upload
│   │   ├── candidate_login.html    # Candidate login (email + phone)
│   │   ├── candidate_dashboard.html# Candidate dashboard + AI suggestions
│   │   ├── candidate_success.html  # Registration success page
│   │   └── interview_prep.html     # Interview Q&A practice page
│   │
│   ├── static/                     # CSS, JS, images
│   │   ├── style.css
│   │   └── script.js
│   │
│   ├── uploads/                    # Uploaded resumes (auto-created)
│   │
│   └── utils/
│       ├── resume_parser.py        # Extract text + skills from resume
│       ├── scorer.py               # Score calculation + interview plan
│       └── mailer.py               # Email notification utility
│
├── .env                            # Environment variables (never commit this)
├── .env.example                    # Example env file for reference
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

---

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/smart_management_interview_system.git
cd smart_management_interview_system
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create `.env` File
```bash
cp .env.example .env
```
Then fill in your values in `.env`.

### 5. Start MongoDB
Make sure MongoDB is running locally:
```bash
mongod
```

### 6. Run the Application
```bash
python app.py
```

Open browser and go to: **http://127.0.0.1:5000**

---

## 🔐 Environment Variables

Create a `.env` file in the root folder with these values:

```env
SECRET_KEY=your_flask_secret_key_here

MONGO_URI=mongodb://localhost:27017/
DB_NAME=smart_interview_db

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

GROQ_API_KEY=your_groq_api_key_here

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
```

> ⚠️ Never push your `.env` file to GitHub. Add it to `.gitignore`.

---

## 🔑 How to Use

### Admin Flow
1. Go to `http://127.0.0.1:5000/admin/login`
2. Login with admin credentials from `.env`
3. View all candidates, their scores, skills, and status

### Candidate Flow
1. Go to `http://127.0.0.1:5000/candidate/register`
2. Fill in name, email, phone, role and upload resume
3. System auto-calculates score and status
4. Go to `http://127.0.0.1:5000/candidate/login`
5. Login with **email + phone number**
6. View your personalized dashboard with AI suggestions

### Interview Preparation
1. Go to `http://127.0.0.1:5000/interview/prep`
2. Enter subject, topic, level, and question type
3. Get 20 AI-generated questions with answers and tips

---

## 📊 Scoring Logic

| Score Range | Status | Interview Plan |
|-------------|--------|----------------|
| 80 – 100 | Selected | Round 1: Technical deep-dive → Round 2: System Design → Round 3: HR |
| 50 – 79 | Selected | Round 1: Technical screening → Round 2: Coding task → Round 3: HR |
| 0 – 49 | Under Review | Round 1: Aptitude + Communication → Round 2: Foundational Technical |

---

## 🤖 Groq AI Integration

This project uses **Groq API** with `llama-3.3-70b-versatile` model for:

1. **Interview Q&A Generation** — 20 questions with answers and tips
2. **Skill Improvement Suggestions** — Personalized tips based on:
   - Candidate's current skills
   - Applied role
   - Interview status (Selected / Under Review)

Get your free Groq API key at: [https://console.groq.com](https://console.groq.com)

---

## 👩‍💻 Developer

**Vanshika**
Smart Interview Management System — Built with Flask, MongoDB & Groq AI

---

## 📄 License

This project is for educational purposes.

