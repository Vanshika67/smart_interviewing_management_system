from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app.utils.mailer import send_selection_email
from app.utils.resume_parser import extract_skills, extract_text
from app.utils.scorer import calculate_score, interview_plan, selection_status

load_dotenv()
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

db_name = os.getenv("DB_NAME", "smart_interview_db")
client = MongoClient(mongo_uri)
db = client[db_name]
candidates_collection = db["candidates"]
admins_collection = db["admins"]


UPLOAD_DIR = Path("app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}

# Roles shown in the Candidate Register form.
ROLE_GROUPS = {
    "Technical": [
        "Java Developer",
        "Software Engineer (Fresher)",
        "Software Developer (Backend)",
        "Frontend Developer",
        "Backend Developer"
        "Full Stack Developer",
        "Python Developer",
        "Data Analyst",
        "Data Scientist",
        "Machine Learning Engineer",
        "DevOps Engineer",
        "QA / Test Engineer",
        "Mobile App Developer (Android / iOS)",
    ],
    "Non-Technical": [
        "HR Executive",
        "Recruiter",
        "Business Analyst",
        "Product Manager",
        "Project Manager",
        "Operations / Admin",
        "Other",
        "Marketing Executive",
        "Sales Executive",
    ],
    "Student Roles": [
        "Intern - Software Development",
        "Intern - Data Science",
        "Intern - Web Development",
        "Graduate Trainee",
    ],
    "Advanced Roles": [
        "Cloud Engineer",
        "Cybersecurity Analyst",
        "AI Engineer",
        "Mobile App Developer (Android / iOS)",
    ],
}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_default_admin() -> None:
    default_username = os.getenv("ADMIN_USERNAME", "admin").strip()
    default_password = os.getenv("ADMIN_PASSWORD", "admin123").strip()
    if not default_username or not default_password:
        return

    existing_admin = admins_collection.find_one({"username": default_username})
    if existing_admin:
        # Keep default credentials usable in local setup by syncing hash when needed.
        existing_hash = existing_admin.get("password_hash", "")
        if not existing_hash or not check_password_hash(existing_hash, default_password):
            admins_collection.update_one(
                {"_id": existing_admin["_id"]},
                 {"$set": {"password_hash": generate_password_hash(default_password)}},
            )
        return
    admins_collection.insert_one(

        
        {
            "username": default_username,
            "password_hash": generate_password_hash(default_password),
            "created_at": datetime.utcnow(),
        }
    )
ensure_default_admin()
def verify_admin_credentials(username: str, password: str) -> bool:
    admin = admins_collection.find_one({"username": username})
    if admin and check_password_hash(admin.get("password_hash", ""), password):

        return True

    # Backward compatibility: if old record has plain password, migrate to hash.
    if admin and admin.get("password") == password:
        admins_collection.update_one(
            {"_id": admin["_id"]},
            {
                "$set": {"password_hash": generate_password_hash(password)},
                "$unset": {"password": ""},
            },
        )
        return True

    # Fallback to .env credentials for easy local setup.
    env_user = os.getenv("ADMIN_USERNAME", "admin").strip()
    env_pass = os.getenv("ADMIN_PASSWORD", "admin123").strip()
    if username == env_user and password == env_pass:
        return True
    # Hard fallback for first-time local testing.
    if username == "admin" and password == "admin123":
        return True
    return False
def generate_questions(subject, topic):
    questions = []

    for i in range(1, 21):
        q = f"What is {topic}? Explain in context of {subject}. (Q{i})"
        a = f"{topic} is an important concept in {subject}. It is used in real-world applications."

        questions.append({
            "question": q,
            "answer": a
        })

    return questions



@app.route("/")
def home():
    return redirect(url_for("admin_login"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if verify_admin_credentials(username, password):
            session["admin_logged_in"] = True
            session["admin_username"] = username
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials", "error")

    default_username = os.getenv("ADMIN_USERNAME", "admin").strip()
    default_password = os.getenv("ADMIN_PASSWORD", "admin123").strip()
    return render_template(
        "admin_login.html",
        default_admin_username=default_username,
        default_admin_password=default_password,
    )


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/candidate/register", methods=["GET", "POST"])
def candidate_register():
    role_groups = ROLE_GROUPS
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "").strip()
        resume = request.files.get("resume")

        if not name or not email or not role or not resume:
            flash("Please fill all required fields and upload resume", "error")
            return render_template("candidate_register.html", role_groups=role_groups)

        if not allowed_file(resume.filename):
            flash("Only PDF, DOCX, TXT, MD files are allowed", "error")
            return render_template("candidate_register.html", role_groups=role_groups)

        safe_name = secure_filename(resume.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        saved_filename = f"{timestamp}_{safe_name}"
        saved_path = UPLOAD_DIR / saved_filename
        resume.save(saved_path)

        raw_text = extract_text(str(saved_path))
        skills = extract_skills(raw_text)
        score = calculate_score(skills)
        plan = interview_plan(score)
        status = selection_status(score)

        candidate_doc = {
            "name": name,
            "email": email,
            "phone": phone,
            "role": role,
            "resume_filename": saved_filename,
            "skills": skills,
            "score": score,
            "interview_plan": plan,
            "status": status,
            "created_at": datetime.utcnow(),
        }
        candidates_collection.insert_one(candidate_doc)

        if status == "Selected":
            send_selection_email(
                smtp_host=os.getenv("SMTP_HOST", ""),
                smtp_port=int(os.getenv("SMTP_PORT", "587")),
                smtp_user=os.getenv("SMTP_USER", ""),
                smtp_password=os.getenv("SMTP_PASSWORD", ""),
                to_email=email,
                candidate_name=name,
            )

        return render_template("candidate_success.html", name=name, status=status)

    return render_template("candidate_register.html", role_groups=role_groups)


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    candidates = list(candidates_collection.find().sort("created_at", -1))
    return render_template(
        "admin_dashboard.html",
        candidates=candidates,
        admin_username=session.get("admin_username", "admin"),
    )
@app.route('/interview_prep', methods=['GET','POST'])
def interview_prep():
    if request.method == 'POST':
        subject = request.form['subject']
        topic = request.form['topic']

        questions = generate_questions(subject, topic)

        prep_collection.insert_one({
            "subject": subject,
            "topic": topic,
            "questions": questions
        })

        return render_template("interview_prep.html",
                               questions=questions,
                               subject=subject,
                               topic=topic)

    return render_template("interview_prep.html")


if __name__ == "__main__":
    app.run(debug=True)
