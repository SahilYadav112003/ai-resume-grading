from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import pdfplumber
import re

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.lower()

def extract_skills(jd):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', jd.lower())
    return list(set(words))

def analyze_resume(text, skills):
    found = [s for s in skills if s in text]
    score = int((len(found)/len(skills))*100) if skills else 0

    if score >= 80:
        decision = "FIT"
    elif score >= 60:
        decision = "MODERATE"
    else:
        decision = "NOT FIT"

    return {
        "score": score,
        "matched_skills": found[:5],
        "missing_skills": list(set(skills)-set(found))[:5],
        "decision": decision
    }

@app.post("/analyze")
async def analyze(jd: str = Form(...), files: List[UploadFile] = File(...)):
    skills = extract_skills(jd)
    results = []

    for file in files:
        text = extract_text(file.file)
        result = analyze_resume(text, skills)

        results.append({
            "name": file.filename,
            **result
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return {"results": results}