import io
import tempfile
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import session, redirect, url_for
import sqlite3
from flask import Flask, request, jsonify, render_template, send_file

from collections import Counter

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from database import init_db, save_resume
from utils import (
    extract_skills,
    predict_job_role,
    calculate_resume_score,
    generate_interview_questions,
    extract_text_from_pdf,
    extract_text_from_docx,
    get_resume_suggestions,
    get_job_recommendations
)
import requests
from dotenv import load_dotenv
import os

load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
print("APP ID:", ADZUNA_APP_ID)
print("API KEY:", ADZUNA_API_KEY)
app = Flask(__name__)
app.secret_key = "ai_placement_secret_key"

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload_page")
def upload_page():
    return render_template("upload.html")


# ================= RESUME ANALYSIS =================
@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():

    
    from flask import jsonify
    

    

        

    file = request.files["file"]

    if file.filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(file)
    elif file.filename.endswith(".docx"):
        resume_text = extract_text_from_docx(file)
    else:
        return jsonify({"error": "Only PDF/DOCX supported"}), 400

    skills = extract_skills(resume_text)
    score = calculate_resume_score(skills)
    job_role, role_scores = predict_job_role(skills)
    questions = generate_interview_questions(skills, job_role)
    suggestions = get_resume_suggestions(skills)
    job_recommendations = get_jobs(job_role,skills)
    resume_skills = [s.lower() for s in skills]
    
    for job in job_recommendations:

        title = job["title"].lower()

        if "frontend" in title:

            required_skills = [
                "HTML",
                "CSS",
                "JavaScript",
                "React",
                "TypeScript"
            ]

        elif "backend" in title:

            required_skills = [
                "Python",
                "Flask",
                "Django",
                "SQL",
                "REST API"
            ]

        else:

            required_skills = [
                "Python",
                "SQL"
            ]

        missing_skills = []

        for skill in required_skills:

            if skill.lower() not in resume_skills:
                missing_skills.append(skill)

        job["required_skills"] = required_skills
        job["missing_skills"] = missing_skills
    

    

    job["required_skills"] = required_skills
    job["missing_skills"] = missing_skills
    print("UPLOAD SUCCESS")
    print(job_role)
    print(score)
    print(skills)
    print(session["user_id"])
    print("SKILLS:", skills)
    print("JOBS FROM ADZUNA:", job_recommendations)
    print(job_recommendations)
    save_resume(job_role, score, skills, session["user_id"])
    
    return jsonify({
        "status": "success",
        "skills_found": skills,
        "resume_score": score,
        "role_scores": role_scores,
        "predicted_role": job_role,
        "job_recommendations": job_recommendations,
        "interview_questions": questions,
        "resume_suggestions": suggestions
    })
def get_jobs(role,skills):
    app_id = os.getenv("ADZUNA_APP_ID")
    api_key = os.getenv("ADZUNA_API_KEY")
    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"

    params = {
        "app_id": app_id,
        "app_key": api_key,
        "what": role,
        "results_per_page": 10
    }

    response = requests.get(url, params=params)
    data = response.json()

    jobs = []

    for job in data.get("results", []):
        jobs.append({
            "title": job.get("title"),
            "company": job.get("company", {}).get("display_name"),
            "location": job.get("location", {}).get("display_name"),
            "salary": job.get("salary_max") or job.get("salary_min") or "Not specified",
            "required_skills": [...],
            "missing_skills": [...]
        })
    print("JOBS WITH SKILLS:", jobs)
    print(jobs)
    return jobs



# ================= ATS GAUGE (IMAGE) =================
def generate_ats_gauge(score):
    path = os.path.join(tempfile.gettempdir(), "ats.png")

    fig, ax = plt.subplots(figsize=(4, 2))
    ax.barh(["ATS Score"], [score], color="green" if score > 60 else "orange" if score > 40 else "red")
    ax.set_xlim(0, 100)
    ax.set_title("ATS Score Gauge")
    plt.tight_layout()

    plt.savefig(path)
    plt.close()

    return path


# ================= PDF REPORT =================
@app.route("/download_report", methods=["POST"])
def download_report():

    data = request.get_json()
    print(data)
    predicted_role = data.get("predicted_role", "")
    resume_score = data.get("resume_score", 0)

    skills_found = data.get("skills_found", [])
    role_scores = data.get("role_scores", {})


    job_recommendations = data.get("job_recommendations", [])
    interview_questions = data.get("interview_questions", [])
    resume_suggestions = data.get("resume_suggestions", [])

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    title = styles["Title"]
    h2 = styles["Heading2"]
    normal = styles["Normal"]

    content = []

    # ================= TITLE =================
    content.append(Paragraph("AI PLACEMENT ANALYSIS REPORT", title))
    content.append(Spacer(1, 10))
 
 

    
    # ================= SCORE BADGE =================
    level = "EXCELLENT" if resume_score >= 75 else "GOOD" if resume_score >= 50 else "NEEDS IMPROVEMENT"
    color = colors.green if resume_score >= 75 else colors.orange if resume_score >= 50 else colors.red

    badge = Table([[f"Score: {resume_score}% | {level}"]], colWidths=[500])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))

    content.append(badge)
    content.append(Spacer(1, 15))
    # ================= ATS SCORE GAUGE =================

    chart_path = os.path.join(tempfile.gettempdir(), "ats_gauge.png")

    fig, ax = plt.subplots(figsize=(4,4))

    ax.pie(
        [resume_score, 100 - resume_score],
        startangle=90,
        colors=["green", "lightgray"],
        wedgeprops={"width":0.3}
    )

    ax.text(
        0,
        0,
        f"{resume_score}%",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold"
    )

    plt.savefig(chart_path, bbox_inches="tight")
    plt.close()

    content.append(Paragraph("ATS SCORE", h2))
    content.append(Image(chart_path, width=180, height=180))
    content.append(Spacer(1, 15))


    # ================= SUMMARY TABLE =================
    summary = [
        ["Field", "Details"],
        ["Role", predicted_role],
        ["Score", f"{resume_score}%"],
        ["Skills", str(len(skills_found))]
    ]

    table = Table(summary, colWidths=[200, 300])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    content.append(table)
    content.append(Spacer(1, 15))
    content.append(Paragraph("ROLE PROBABILITY", h2))
    content.append(Spacer(1, 5))

    for role, score in role_scores.items():
  
        content.append(
            Paragraph(
                f"{role} : {score}%",
                normal
            )
        )

    content.append(Spacer(1, 15))
    # ================= SKILLS =================
    content.append(Paragraph("SKILLS", h2))
    content.append(Spacer(1, 5))
    content.append(Paragraph(" • ".join(skills_found), normal))
    content.append(Spacer(1, 15))

    # ================= SKILL FREQUENCY =================
    skill_weights = {
        "python": 5,
        "java": 4,
        "c": 2,
        "c++": 2,
        "html": 3,
        "css": 3,
        "javascript": 4,
        "react": 4,
        "sql": 4,
        "ai": 5,
        "machine learning": 5,
        "data science": 5
    } 

    labels = []
    values = []

    for skill in skills_found:
        s = skill.lower()
        labels.append(s)
        values.append(skill_weights.get(s, 1))

    # ================= PIE CHART =================
    pie_path = os.path.join(tempfile.gettempdir(), "pie.png")
    plt.figure()
    if values:
        plt.pie(values, labels=labels, autopct="%1.0f%%")
    else:
        plt.text(0.5, 0.5, "No Skills Found", ha="center")
    
    plt.title("Skill Distribution")
    plt.savefig(pie_path)
    plt.close()

    # ================= BAR CHART =================
   

    # ================= RADAR CHART =================
    skill_groups = {
        "Frontend Developer": ["html","css","javascript","react"],

        "Backend Developer": ["python","flask","django","sql"],

        "Data Scientist": ["python","machine learning","pandas","numpy"],

        "Full Stack Developer": ["html","css","javascript","react","python","sql"],

        "AI Engineer": ["python","machine learning","deep learning","tensorflow"],

        "Java Developer": ["java","spring","hibernate"],

        "Data Analyst": ["sql","excel","power bi","tableau"],

        "Cloud Engineer": ["aws","azure","docker","kubernetes"]
    }

    skills_lower = [s.lower() for s in skills_found]

    radar_labels = list(skill_groups.keys())
    radar_values = []

    for group, group_skills in skill_groups.items():
        radar_values.append(sum(1 for s in skills_lower if s in group_skills))

    if sum(radar_values) == 0:
        radar_values = [1, 1, 1]

    radar_path = os.path.join(tempfile.gettempdir(), "radar.png")

    angles = np.linspace(0, 2 * np.pi, len(radar_labels), endpoint=False).tolist()
    radar_values += radar_values[:1]
    angles += angles[:1]

    

    # ================= ADD IMAGES =================
    content.append(Paragraph("VISUAL ANALYSIS", h2))
    #content.append(Image(chart_path, width=120, height=120))
    content.append(Image(pie_path, width=250, height=250))
    #content.append(Image(bar_path, width=300, height=200))
    #content.append(Image(radar_path, width=300, height=250))
    content.append(Paragraph("JOB SUGGESTIONS",h2))
    for job in job_recommendations:

        title = job.get("title", "")
        company = job.get("company", "")
        location = job.get("location", "")
        salary = job.get("salary", "Not specified")

        required_skills = ", ".join(
            job.get("required_skills", [])
        )

        missing_skills = ", ".join(
            job.get("missing_skills", [])
        )

        content.append(
            Paragraph(
                f"<b>{title}</b>",
                normal
            )
        )

        content.append(
            Paragraph(
                f"Company: {company}",
                normal
            )
        )

        content.append(
            Paragraph(
                f"Location: {location}",
                normal
            )
        )

        content.append(
            Paragraph(
                f"Salary: {salary}",
                normal
            )
        )

        content.append(
            Paragraph(
                f"Required Skills: {required_skills}",
                normal
            )
        )

        content.append(
            Paragraph(
                f"Missing Skills: {missing_skills}",
                normal
            )
        )

        content.append(Spacer(1,10))
    content.append(Paragraph("INTERVIEW QUESTIONS", h2))
    content.append(Spacer(1, 5))

    for q in interview_questions:
        content.append(Paragraph("• " + q, normal))

    content.append(Spacer(1, 15))




    # ================= SUGGESTIONS =================
    content.append(Paragraph("IMPROVEMENT PLAN", h2))
    for s in resume_suggestions:
        content.append(Paragraph("• " + s, normal))
    
    content.append(Spacer(1, 40))

    content.append(
        Paragraph(
            "<para align='center'><font size='15'><b>Thank You</b></font></para>",
            normal
        )
    )

    content.append(
        Paragraph(
            "<para align='center'>Generated by AI Placement Assistant</para>",
            
            normal
        )
    )
    # ================= BUILD PDF =================
    doc.build(content)
    buffer.seek(0)

    # cleanup
    for f in [chart_path, pie_path]:
        if os.path.exists(f):
            os.remove(f)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="AI_Placement_Report.pdf",
        mimetype="application/pdf"
    )
@app.route("/history")
def history():

    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT role, score, skills, timestamp 
    FROM resumes 
    WHERE user_id = ? 
    ORDER BY id DESC
    """, (session["user_id"],))

    rows = cursor.fetchall()
    conn.close()

    data = []

    for r in rows:
        data.append({
            "role": r[0],
            "score": r[1],
            "skills": r[2],
            "timestamp": r[3]
        })

    return jsonify(data)
@app.route("/history_page")
def history_page():
    return render_template("history.html")
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json

    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (username, password))
        conn.commit()
        return jsonify({"message": "Signup successful"})
    except:
        return jsonify({"error": "User already exists"})
    finally:
        conn.close()
@app.route("/login", methods=["POST"])
def login():
    data = request.json

    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username=? AND password=?",
                   (username, password))

    user = cursor.fetchone()
    conn.close()

    if user:
        session["user_id"] = user[0]
        session["username"] = username
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"error": "Invalid credentials"})
@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})
@app.route("/login_page")
def login_page():
    return render_template("login.html")
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
@app.route("/analytics")
def analytics():

    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT score, role, timestamp 
    FROM resumes 
    WHERE user_id = ?
    ORDER BY id ASC
    """, (session["user_id"],))

    rows = cursor.fetchall()
    conn.close()

    scores = [r[0] for r in rows]
    roles = [r[1] for r in rows]
    dates = [r[2] for r in rows]

    return jsonify({
        "scores": scores,
        "roles": roles,
        "dates": dates
    })
@app.route("/analytics_page")
def analytics_page():
    return render_template("analytics.html")
@app.route("/compare")
def compare():

    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT score, timestamp
    FROM resumes
    WHERE user_id = ?
    ORDER BY id DESC
    LIMIT 2
    """, (session["user_id"],))

    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 2:
        return jsonify({
            "message": "Upload at least 2 resumes"
        })

    current_score = rows[0][0]
    previous_score = rows[1][0]

    improvement = current_score - previous_score

    return jsonify({
        "previous_score": previous_score,
        "current_score": current_score,
        "improvement": improvement
    })
@app.route("/ats_match", methods=["POST"])
def ats_matching():

    data = request.get_json()

    resume_skills = data.get("skills", [])
    job_description = data.get("job_description", "")

    score, matched, missing = ats_match(
        resume_skills,
        job_description
    )

    return jsonify({
        "ats_score": score,
        "matched_skills": matched,
        "missing_skills": missing
    })
def ats_match(resume_skills, job_description):

    jd = job_description.lower()

    common_skills = [
        "python", "java", "sql",
        "html", "css", "javascript",
        "react", "flask", "django",
        "git", "machine learning",
        "ai", "data science"
    ]

    # Skills required by the job description
    jd_skills = []

    for skill in common_skills:
        if skill in jd:
            jd_skills.append(skill)

    matched = []
    missing = []

    resume_lower = [s.lower() for s in resume_skills]

    for skill in jd_skills:

        if skill in resume_lower:
            matched.append(skill)
        else:
            missing.append(skill)

    # If no recognizable skills are found in JD
    if len(jd_skills) == 0:
        return 0, [], ["No technical skills found in Job Description"]

    score = int((len(matched) / len(jd_skills)) * 100)

    return score, matched, missing
@app.route("/ats_page")
def ats_page():
    return render_template("ats.html")


# ================= RUN =================
if __name__ == "__main__":
    init_db()
    app.run(debug=True,use_reloader=False)
