# 🚀 GFI ATS Prototype

An AI-powered Applicant Tracking System (ATS) prototype built for the Growth For Impact Software Engineering assignment. This system automates resume ingestion, extraction, and candidate ranking against specific job descriptions using LLM Structured Outputs, featuring a highly responsive Next.js dashboard and a Vercel-hosted FastAPI backend.

## ✨ Features

- **Automated Resume Parsing:** Extracts skills, experience, education, and projects from raw `.docx` and `.pdf` files.
- **Deterministic AI Scoring:** Evaluates candidates against two distinct roles (LifeCycle Assessment vs. UI/UX Design) using a strict prompt rubric and OpenAI's `gpt-4o-mini`.
- **Clean Data Guarantee:** Leverages Pydantic and OpenAI Structured Outputs to ensure the LLM returns 100% clean, parseable JSON, completely eliminating frontend formatting crashes.
- **Live Testing UI:** HR reviewers can upload unseen resumes directly through the Next.js dashboard. The FastAPI backend processes the file entirely in-memory and updates the ranking live.
- **Explainable AI:** Provides human-readable, 1-2 sentence evidence-based reasoning for every score to support manual HR review.

## 🛠️ Tech Stack

- **Frontend:** Next.js (React), Tailwind CSS, Lucide Icons
- **Backend:** FastAPI, Python (Serverless on Vercel)
- **AI & Data:** OpenAI API (`gpt-4o-mini`), Pydantic (Structured Outputs)
- **Document Parsing:** `python-docx`, `pypdf`
- **Offline Ingestion:** Scrapling (for bypassing UI bot protections)

## 🚀 Quick Start (Local Development)

### 1. Clone the Repository
```bash
git clone [https://github.com/abaank7/gfi-ats-prototype.git](https://github.com/abaank7/gfi-ats-prototype.git)
cd gfi-ats-prototype
```

### 2. Backend Setup (FastAPI)
Create a `.env` file in the root directory and add your OpenAI API key:
```env
OPENAI_API_KEY=your_openai_api_key_here
```
Activate your Python environment (using `uv` or standard `venv`) and install the serverless dependencies:
```bash
uv pip install -r requirements.txt
uvicorn api.index:app --reload --port 8000
```

### 3. Frontend Setup (Next.js)
Open a new terminal window and run:
```bash
npm install
npm run dev
```
Visit `http://localhost:3000` to view the dashboard and test live uploads.

## 🧠 Methodology & Architecture

1. **Data Ingestion:** Used `Scrapling` in an offline pipeline to bypass Zoho's dynamic JS rendering, downloading the 47 resumes directly as binary files to avoid Vercel timeouts.
2. **Extraction & Sanitization:** Parsed resumes with `python-docx` and passed raw text to OpenAI. To avoid standard LLM hallucination risks, strict Pydantic schemas were enforced.
3. **Serverless Live Uploads:** The Next.js frontend sends live `.pdf`/`.docx` uploads to the Vercel-hosted FastAPI endpoint. The backend extracts text in-memory via `io.BytesIO` (respecting Vercel's 250MB size and read-only filesystem limits), scores the candidate, and returns clean JSON. 
4. **Client-Side Persistence:** The UI uses browser `localStorage` to persist these uploaded test candidates across page refreshes without requiring a dedicated cloud database instance.

## 👤 Author

**Abaan Koul**
- Email: [abaankoul31@gmail.com](mailto:abaankoul31@gmail.com)
- GitHub: [@abaank7](https://github.com/abaank7)