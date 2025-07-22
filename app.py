from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import fitz  # PyMuPDF
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

# ✅ UPDATED FUNCTION
def analyze_resume(resume_text, job_title):
    if not OPENROUTER_API_KEY:
        raise Exception("API Key not loaded. Check your .env file for OPENROUTER_API_KEY.")
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

    prompt = f"""
You are an expert HR recruiter.

Resume:
{resume_text}

Job Title: {job_title}

Please provide:
1. Match score (0 to 100)
2. 3 key strengths
3. 2 weaknesses or missing skills
4. Is this a good fit? (yes/no + reason)
5. 5 interview questions
"""

    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:5000",  # Update if deploying
                "X-Title": "Resume Analyzer",
            },
            model="deepseek/deepseek-chat-v3-0324:free",  # You can try other models too
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"OpenRouter API Error: {str(e)}")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files or "job_title" not in request.form:
        return jsonify({"error": "Missing resume or job title"}), 400

    file = request.files["resume"]
    job_title = request.form["job_title"]

    try:
        resume_text = extract_text_from_pdf(file)
        result = analyze_resume(resume_text, job_title)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    from waitress import serve
    print("Loaded API Key:", OPENROUTER_API_KEY)
    serve(app, host="0.0.0.0", port=8080)
@app.route('/bulk_analyze', methods=['POST'])
def bulk_analyze():
    uploaded_files = request.files.getlist("resumes")
    results = []

    for file in uploaded_files:
        if file:
            filename = file.filename
            text = extract_text_from_resume(file)  # You must already have this
            prediction = analyze_resume(text)      # Your existing AI logic
            results.append({'name': filename, 'score': prediction})

    ranked = sorted(results, key=lambda x: x['score'], reverse=True)
    top_10 = ranked[:10]

    return render_template('bulk_result.html', results=top_10)
