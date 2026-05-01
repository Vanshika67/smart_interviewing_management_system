# Smart Interview Management Project

This project uses:
- Backend: Flask (Python)
- Database: MongoDB
- Frontend: HTML, CSS, JavaScript

## Features
- Admin login with username and password
- Default admin creation in MongoDB (on first run)
- Candidate registration with resume upload
- Resume skill extraction and score calculation
- Interview plan generation based on score
- Selection status and auto email notification for selected candidates
- Admin dashboard to view all candidate details

## Project Structure
```text
smart_management_interview_project/
|-- app.py
|-- requirements.txt
|-- .env.example.txt
|-- README.md
|-- app/
|   |-- static/
|   |   |-- style.css
|   |   `-- script.js
|   |-- templates/
|   |   |-- base.html
|   |   |-- admin_login.html
|   |   |-- candidate_register.html
|   |   |-- candidate_success.html
|   |   `-- admin_dashboard.html
|   |-- uploads/
|   `-- utils/
|       |-- resume_parser.py
|       |-- scorer.py
|       `-- mailer.py
`-- resume_parser.py
```

## Setup
1. Create and activate virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example.txt` to `.env` and update values.
4. Start MongoDB locally.
5. Run project:
   ```bash
   python app.py
   ```

### Default Admin Login
If you don’t set `ADMIN_USERNAME` / `ADMIN_PASSWORD` in `.env`, the app uses:
- Username: `admin`
- Password: `admin123`

On a fresh MongoDB database, the app seeds this default admin automatically at startup.

## Default Admin Flow
- On first run, `app.py` creates one admin user in MongoDB using:
  - `ADMIN_USERNAME`
  - `ADMIN_PASSWORD`
- Password is stored as a hash, not plain text.

## Main Routes
- `/admin/login` -> Admin login page
- `/admin/dashboard` -> Admin dashboard
- `/admin/logout` -> Logout admin
- `/candidate/register` -> Candidate registration form

## Candidate Processing Flow
1. Candidate fills form and uploads resume.
2. Resume text is extracted (`PDF/DOCX/TXT/MD`).
3. Skills are detected from known skill list.
4. Score is calculated from required skills.
5. Interview plan is created from score.
6. If selected, email is sent automatically.
7. Data is saved to MongoDB and shown in dashboard.
