def extract_skills(resume_text):
    skills_db = [
        "python", "java", "c", "c++", "sql",
        "machine learning", "deep learning",
        "html", "css", "javascript",
        "react", "flask", "django",
        "ai", "data science"
    ]

    resume_text = resume_text.lower()

    found_skills = []

    for skill in skills_db:
        if skill in resume_text:
            found_skills.append(skill)

    return found_skills

def calculate_resume_score(skills):
    skills = [s.lower() for s in skills]

    score_map = {
        "python": 15,
        "java": 10,
        "c": 5,
        "c++": 5,
        "sql": 10,
        "machine learning": 20,
        "deep learning": 20,
        "ai": 15,
        "data science": 15,
        "flask": 10,
        "django": 10,
        "html": 5,
        "css": 5,
        "javascript": 10,
        "react": 10
    }

    score = 0

    for skill in skills:
        if skill in score_map:
            score += score_map[skill]

    return min(score, 100)
def generate_interview_questions(skills, role):
    questions = []

    skills = [s.lower() for s in skills]

    if "python" in skills:
        questions += [
            "What is the difference between List and Tuple?",
            "Explain *args and **kwargs.",
            "What are decorators in Python?",
            "Explain Python OOP concepts.",
            "How does exception handling work?"
        ]

    if "sql" in skills:
        questions += [
            "What is the difference between WHERE and HAVING?",
            "Explain joins in SQL."
        ]

    if "machine learning" in skills or "ai" in skills:
        questions += [
            "What is overfitting?",
            "Explain supervised vs unsupervised learning."
        ]

    if role == "Backend Developer":
        questions += [
            "What is REST API?",
            "What is Flask or Django used for?"
        ]

    if role == "Data Scientist":
        questions += [
            "What is feature engineering?",
            "What is model training?"
        ]

    if not questions:
        questions.append("Tell me about your project experience.")

    return questions
import PyPDF2

def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""

    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()

    return text
from docx import Document

def extract_text_from_docx(file):
    doc = Document(file)

    text = ""

    for para in doc.paragraphs:
        text += para.text + "\n"

    return text
def get_resume_suggestions(skills):
    suggestions = []

    if "sql" not in skills:
        suggestions.append("Learn SQL and add database projects.")

    if "python" not in skills:
        suggestions.append("Learn Python for technical roles.")

    if "machine learning" not in skills:
        suggestions.append("Add Machine Learning skills or projects.")

    if "javascript" not in skills:
        suggestions.append("Learn JavaScript for web development opportunities.")

    if len(skills) < 5:
        suggestions.append("Add more technical skills to strengthen your resume.")

    suggestions.append("Add GitHub profile link.")
    suggestions.append("Include certifications and internships.")
    suggestions.append("Add 2-3 strong academic or personal projects.")

    return suggestions
def predict_job_role(skills):

    skills = [s.lower().strip() for s in skills]

    scores = {
        "Frontend Developer": 0,
        "Backend Developer": 0,
        "Data Scientist": 0
    }

    frontend = {"html", "css", "javascript", "react"}
    backend = {"java", "sql", "flask", "django", "c"}
    data = {"python", "ai", "machine learning", "data science"}

    for s in skills:
        if s in frontend:
            scores["Frontend Developer"] += 1
        if s in backend:
            scores["Backend Developer"] += 1
        if s in data:
            scores["Data Scientist"] += 1

    max_score = max(scores.values()) if max(scores.values()) > 0 else 1

    for k in scores:
        scores[k] = round((scores[k] / max_score) * 100)

    best_role = max(scores, key=scores.get)

    return best_role, scores
import requests

def get_job_recommendations(job_role, skills):

    APP_ID = "YOUR_APP_ID"
    APP_KEY = "YOUR_APP_KEY"

    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": job_role,
        "results_per_page": 5
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            jobs = response.json()["results"]

            return [
                {
                    "title": job["title"],
                    "company": job["company"]["display_name"],
                    "location": job["location"]["display_name"]
                }
                for job in jobs
            ]

    except Exception as e:
        print(e)

    return []







