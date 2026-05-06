from __future__ import annotations

import os
import json
from datetime import datetime
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app.utils.mailer import send_selection_email
from app.utils.resume_parser import extract_skills, extract_text
from app.utils.scorer import calculate_score, interview_plan, selection_status

load_dotenv(override=True)

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
db_name   = os.getenv("DB_NAME", "smart_interview_db")

mongo_client          = MongoClient(mongo_uri)
db                    = mongo_client[db_name]
candidates_collection = db["candidates"]
admins_collection     = db["admins"]
prep_collection       = db["interview_prep"]

# Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

UPLOAD_DIR = Path("app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}

ROLE_GROUPS = {
    "Technical": [
        "Java Developer",
        "Software Engineer (Fresher)",
        "Software Developer (Backend)",
        "Frontend Developer",
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


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_default_admin():
    default_username = os.getenv("ADMIN_USERNAME", "admin").strip()
    default_password = os.getenv("ADMIN_PASSWORD", "admin123").strip()
    if not default_username or not default_password:
        return
    existing_admin = admins_collection.find_one({"username": default_username})
    if existing_admin:
        existing_hash = existing_admin.get("password_hash", "")
        if not existing_hash or not check_password_hash(existing_hash, default_password):
            admins_collection.update_one(
                {"_id": existing_admin["_id"]},
                {"$set": {"password_hash": generate_password_hash(default_password)}},
            )
        return
    admins_collection.insert_one({
        "username": default_username,
        "password_hash": generate_password_hash(default_password),
        "created_at": datetime.utcnow(),
    })


ensure_default_admin()


def verify_admin_credentials(username, password):
    admin = admins_collection.find_one({"username": username})
    if admin and check_password_hash(admin.get("password_hash", ""), password):
        return True
    if admin and admin.get("password") == password:
        admins_collection.update_one(
            {"_id": admin["_id"]},
            {"$set": {"password_hash": generate_password_hash(password)},
             "$unset": {"password": ""}},
        )
        return True
    env_user = os.getenv("ADMIN_USERNAME", "admin").strip()
    env_pass = os.getenv("ADMIN_PASSWORD", "admin123").strip()
    if username == env_user and password == env_pass:
        return True
    if username == "admin" and password == "admin123":
        return True
    return False


def generate_questions_via_groq(subject, topic, level, qtype):
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in .env file")

    topic_line = topic if topic else "all important topics in " + subject

    prompt = (
        'You are an expert technical interviewer.\n'
        'Generate exactly 20 interview questions for:\n'
        '- Subject: "' + subject + '"\n'
        '- Topic: "' + topic_line + '"\n'
        '- Level: ' + level + '\n'
        '- Question type: ' + qtype + '\n\n'
        'Rules:\n'
        '1. Return ONLY a valid JSON array, no markdown, no explanation\n'
        '2. Each item must have exactly 3 keys: "question", "answer", "tip"\n'
        '3. "answer" should be 3-5 sentences\n'
        '4. "tip" should be one short interview tip\n'
        '5. Generate all 20 questions\n\n'
        '[\n  {"question": "...", "answer": "...", "tip": "..."}\n]\n'
    )

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    return json.loads(raw)


# ─────────────────────────────────────────────────────────────────────────────
# NEW: Groq-powered AI skill suggestions for candidate dashboard
# ─────────────────────────────────────────────────────────────────────────────

def generate_skill_suggestions_via_groq(candidate):
    """
    Use Groq API to generate personalized skill improvement suggestions.
    - If Selected   → skills to grow in their company/industry for promotion
    - If Not Selected → skills to improve to crack next interview
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    status  = candidate.get("status", "Under Review")
    role    = candidate.get("role", "Software Engineer")
    skills  = candidate.get("skills", [])
    skills_str = ", ".join(skills) if skills else "Not specified"

    if status == "Selected":
        prompt = (
            f"A candidate has been SELECTED for the role of '{role}'.\n"
            f"Their current skills are: {skills_str}.\n\n"
            "Generate exactly 6 personalized skill improvement tips to help them "
            "grow in their company, get promoted faster, and excel in their industry.\n\n"
            "Rules:\n"
            "1. Return ONLY a valid JSON array, no markdown, no explanation.\n"
            "2. Each item must have 2 keys: \"skill\" and \"reason\".\n"
            "3. \"reason\" must be 1-2 sentences explaining why it helps for promotion.\n\n"
            "Example format:\n"
            '[{"skill": "System Design", "reason": "Helps you handle large-scale projects and get promoted to senior roles faster."}]\n'
        )
    else:
        prompt = (
            f"A candidate was NOT SELECTED for the role of '{role}'.\n"
            f"Their current skills are: {skills_str}.\n\n"
            "Generate exactly 6 personalized skill improvement tips to help them "
            "improve and crack their next interview for this role.\n\n"
            "Rules:\n"
            "1. Return ONLY a valid JSON array, no markdown, no explanation.\n"
            "2. Each item must have 2 keys: \"skill\" and \"reason\".\n"
            "3. \"reason\" must be 1-2 sentences explaining why it helps crack the next interview.\n\n"
            "Example format:\n"
            '[{"skill": "Data Structures", "reason": "Most interview questions test DS fundamentals. Strengthening this will boost your coding round performance."}]\n'
        )

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        return json.loads(raw)
    except Exception:
        # Fallback suggestions if API fails
        if status == "Selected":
            return [
                {"skill": "System Design", "reason": "Helps you handle large-scale projects and grow to senior roles."},
                {"skill": "Cloud Computing (AWS/GCP/Azure)", "reason": "Most companies now run on cloud — essential for promotion."},
                {"skill": "DevOps & CI/CD", "reason": "Automate deployments and increase team productivity."},
                {"skill": "Leadership & Communication", "reason": "Soft skills separate good engineers from great ones."},
                {"skill": "Docker & Kubernetes", "reason": "Container knowledge is in demand across all tech companies."},
                {"skill": "Code Review Best Practices", "reason": "Reviewing others' code builds credibility and visibility."},
            ]
        else:
            return [
                {"skill": "Data Structures & Algorithms", "reason": "Foundation of every coding interview — practice daily."},
                {"skill": "Problem Solving (LeetCode/HackerRank)", "reason": "Consistent practice improves speed and accuracy."},
                {"skill": "Communication Skills", "reason": "Clear explanation of your thinking impresses interviewers."},
                {"skill": "System Design Basics", "reason": "Even for junior roles, basic SD knowledge is valued."},
                {"skill": "Mock Interviews", "reason": "Simulating real interviews reduces anxiety and builds confidence."},
                {"skill": "Resume Building", "reason": "A strong resume increases your chances of getting shortlisted."},
            ]


# ─────────────────────────────────────────────────────────────────────────────
# EXISTING ROUTES (unchanged from your original working code)
# ─────────────────────────────────────────────────────────────────────────────

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
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    return redirect(url_for("admin_login"))


@app.route("/candidate/register", methods=["GET", "POST"])
def candidate_register():
    role_groups = ROLE_GROUPS
    if request.method == "POST":
        name   = request.form.get("name", "").strip()
        email  = request.form.get("email", "").strip()
        phone  = request.form.get("phone", "").strip()
        role   = request.form.get("role", "").strip()
        resume = request.files.get("resume")

        if not name or not email or not role or not resume:
            flash("Please fill all required fields and upload resume", "error")
            return render_template("candidate_register.html", role_groups=role_groups)

        if not allowed_file(resume.filename):
            flash("Only PDF, DOCX, TXT, MD files are allowed", "error")
            return render_template("candidate_register.html", role_groups=role_groups)

        safe_name      = secure_filename(resume.filename)
        timestamp      = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        saved_filename = f"{timestamp}_{safe_name}"
        saved_path     = UPLOAD_DIR / saved_filename
        resume.save(saved_path)

        raw_text = extract_text(str(saved_path))
        skills   = extract_skills(raw_text)
        score    = calculate_score(skills)
        plan     = interview_plan(score)
        status   = selection_status(score)

        candidate_doc = {
            "name": name, "email": email, "phone": phone, "role": role,
            "resume_filename": saved_filename, "skills": skills,
            "score": score, "interview_plan": plan, "status": status,
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


@app.route("/interview/prep", methods=["GET"])
def interview_prep():
    return render_template("interview_prep.html")


@app.route("/interview/prep/generate", methods=["POST"])
def interview_prep_generate():
    data    = request.get_json(force=True)
    subject = data.get("subject", "").strip()
    topic   = data.get("topic", "").strip()
    level   = data.get("level", "fresher/beginner")
    qtype   = data.get("qtype", "mixed")

    if not subject:
        return jsonify({"error": "Subject required"}), 400

    try:
        questions = generate_questions_via_groq(subject, topic, level, qtype)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    prep_collection.insert_one({
        "subject": subject, "topic": topic, "level": level,
        "qtype": qtype, "questions": questions,
        "created_at": datetime.utcnow(),
    })

    return jsonify({"questions": questions, "subject": subject, "topic": topic})


# ─────────────────────────────────────────────────────────────────────────────
# NEW ROUTES: Candidate Login + Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/candidate/login", methods=["GET", "POST"])
def candidate_login():
    """
    Candidate logs in with Email + Phone number.
    No password needed — matches on email + phone stored during registration.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()

        # Case-insensitive email match
        candidate = candidates_collection.find_one({
            "email": {"$regex": f"^{email}$", "$options": "i"},
            "phone": phone
        })

        if candidate:
            session["candidate_id"]   = str(candidate["_id"])
            session["candidate_name"] = candidate.get("name", "Candidate")
            return redirect(url_for("candidate_dashboard"))
        else:
            flash("Invalid email or phone number. Please check and try again.", "error")

    return render_template("candidate_login.html")


@app.route("/candidate/logout")
def candidate_logout():
    session.pop("candidate_id", None)
    session.pop("candidate_name", None)
    return redirect(url_for("candidate_login"))


@app.route("/candidate/dashboard")
def candidate_dashboard():
    """
    Candidate Dashboard showing:
    - Resume score & skills
    - Interview status (Selected / Under Review)
    - Interview plan
    - Groq AI-powered skill improvement suggestions
    """
    if not session.get("candidate_id"):
        return redirect(url_for("candidate_login"))

    candidate = candidates_collection.find_one(
        {"_id": ObjectId(session["candidate_id"])}
    )
    if not candidate:
        flash("Session expired. Please login again.", "error")
        session.pop("candidate_id", None)
        return redirect(url_for("candidate_dashboard"))

    # Generate AI suggestions via Groq
    suggestions = generate_skill_suggestions_via_groq(candidate)

    return render_template(
        "candidate_dashboard.html",
        candidate=candidate,
        suggestions=suggestions,
    )
    
# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
       

  
