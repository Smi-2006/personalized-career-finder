from flask import Flask, render_template, request, session
from dotenv import load_dotenv
import os
import requests

from firebase import db
from prompt_builder import build_prompt

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "career_secret_key")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ---------------- CAREERS FROM GROQ (COURSE + STRENGTHS BASED) ----------------
def get_careers_for_course(course, strengths):
    prompt = f"""
    A student has completed the course: {course}
    The student's strengths are: {strengths}

    List 5 to 6 suitable career options that match BOTH the course and the student's strengths.
    Format strictly as:
    Career Name – One line explanation.
    """

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "You are a career guidance assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
    )

    text = response.json()["choices"][0]["message"]["content"]

    careers = []
    for line in text.split("\n"):
        if "–" in line:
            line = line.replace("**", "").strip()
            if "." in line[:3]:
                line = line.split(".", 1)[1].strip()

            title, desc = line.split("–", 1)
            careers.append({
                "title": title.strip(),
                "description": desc.strip()
            })

    return careers[:6]

# ---------------- HOME ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- COURSE RECOMMENDATION ----------------
@app.route("/recommend", methods=["POST"])
def recommend():
    interests_list = request.form.getlist("interests")
    strengths_list = request.form.getlist("strengths")

    student = {
        "name": request.form["name"],
        "interests": ", ".join(interests_list),
        "strengths": ", ".join(strengths_list),
        "income": request.form["income"],
        "user_location": request.form["user_location"]
    }

    # store strengths in session for career personalization
    session["strengths"] = student["strengths"]

    # fetch courses from Firestore
    course_docs = db.collection("courses").stream()
    all_courses = [doc.to_dict()["courseName"] for doc in course_docs]

    # build personalized prompt
    prompt = build_prompt(student, all_courses)

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "You are a career guidance assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4
        }
    )

    ai_text = response.json()["choices"][0]["message"]["content"]

    courses = []
    for line in ai_text.split("\n"):
        if "–" in line:
            line = line.replace("**", "").strip()
            if "." in line[:3]:
                line = line.split(".", 1)[1].strip()

            name, explanation = line.split("–", 1)
            courses.append({
                "name": name.strip(),
                "explanation": explanation.strip()
            })

    return render_template(
        "results.html",
        courses=courses,
        user_location=student["user_location"]
    )

# ---------------- COLLEGES + STRENGTH-BASED CAREERS ----------------
@app.route("/colleges")
def colleges():
    course = request.args.get("course")
    user_location = request.args.get("user_location")
    strengths = session.get("strengths", "")

    college_docs = db.collection("colleges").stream()
    colleges = []

    for doc in college_docs:
        c = doc.to_dict()
        if c.get("courseName", "").lower() == course.lower():
            clg_loc = c.get("location")
            usr_loc = user_location.strip() if user_location else None

            if clg_loc and usr_loc:
                c["distance"] = "Nearby" if clg_loc.lower() == usr_loc.lower() else "Different area"
            else:
                c["distance"] = "Location not available"

            colleges.append(c)

    # Careers personalized by course + strengths
    careers = get_careers_for_course(course, strengths)

    return render_template(
        "colleges.html",
        course=course,
        colleges=colleges,
        careers=careers
    )

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
