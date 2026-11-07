import os
import re
from io import BytesIO
from typing import List
import docx
from pypdf import PdfReader

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

# READ AND UNDERSTAND THIS CODE TOO

load_dotenv()

app = FastAPI(
    title="GFI ATS Prototype API",
    description="Serverless FastAPI backend for live resume parsing, classification, and ranking.",
)

# Enable CORS for local Next.js development and Vercel preview deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 1. STRICT PYDANTIC SCHEMA
# ==========================================

from offline_pipeline.schema import CandidateEvaluation


# ==========================================
# 2. IN-MEMORY PARSING FUNCTIONS
# ==========================================
def extract_text_from_docx_bytes(file_bytes: bytes) -> str:
    """Extracts paragraphs and deduplicated table cells from a DOCX byte stream."""
    doc = docx.Document(BytesIO(file_bytes))
    full_text: List[str] = []

    # 1. Standard paragraphs
    for para in doc.paragraphs:
        clean_text = para.text.strip()
        if clean_text:
            full_text.append(clean_text)

    # 2. Tables (deduplicating merged cells)
    for table in doc.tables:
        for row in table.rows:
            seen_cells = set()
            row_data = []
            for cell in row.cells:
                cell_text = " ".join(cell.text.split())
                if cell_text and cell_text not in seen_cells:
                    seen_cells.add(cell_text)
                    row_data.append(cell_text)
            if row_data:
                full_text.append(" | ".join(row_data))

    return "\n".join(full_text)


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Extracts text from all pages of a PDF byte stream."""
    reader = PdfReader(BytesIO(file_bytes))
    full_text: List[str] = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text and page_text.strip():
            full_text.append(page_text.strip())

    return "\n".join(full_text)


# ==========================================
# 3. DETERMINISTIC POST-PROCESSING (CLEANING)
# ==========================================
def clean_candidate_data(
    raw_dict: dict, filename: str, source_link: str = "#uploaded-live"
) -> dict:
    """
    Sanitizes, deduplicates, and clamps LLM output to guarantee clean data for the UI.
    """
    # Deduplicate and strip skills while preserving order
    seen_skills = set()
    cleaned_skills = []
    for skill in raw_dict.get("skills", []):
        clean_s = re.sub(r"\s+", " ", str(skill)).strip()
        if clean_s and clean_s.lower() not in seen_skills:
            seen_skills.add(clean_s.lower())
            cleaned_skills.append(clean_s)

    # Clean projects list
    cleaned_projects = [
        re.sub(r"\s+", " ", str(proj)).strip()
        for proj in raw_dict.get("projects", [])
        if str(proj).strip()
    ][:6]

    # Clamp numeric values to valid bounds
    exp = max(0.0, round(float(raw_dict.get("total_years_experience", 0.0)), 1))
    lca_score = max(0, min(100, int(raw_dict.get("lca_score", 0))))
    ui_ux_score = max(0, min(100, int(raw_dict.get("ui_ux_score", 0))))

    valid_classifications = {"LCA", "UI/UX", "Both", "Neither/Uncertain"}
    classification = raw_dict.get("classification", "Neither/Uncertain")
    if classification not in valid_classifications:
        classification = "Neither/Uncertain"

    return {
        "filename": filename,
        "status": raw_dict.get("status", "SUCCESS"),
        "skills": cleaned_skills[:20],
        "total_years_experience": exp,
        "education": re.sub(
            r"\s+", " ", str(raw_dict.get("education", "Not Specified"))
        ).strip()
        or "Not Specified",
        "projects": cleaned_projects,
        "classification": classification,
        "lca_score": lca_score,
        "lca_reasoning": re.sub(
            r"\s+", " ", str(raw_dict.get("lca_reasoning", ""))
        ).strip(),
        "ui_ux_score": ui_ux_score,
        "ui_ux_reasoning": re.sub(
            r"\s+", " ", str(raw_dict.get("ui_ux_reasoning", ""))
        ).strip(),
        "source_link": source_link,
    }


def build_error_response(filename: str, reason: str) -> dict:
    """Returns a standardized fallback object when extraction or evaluation fails."""
    return {
        "filename": filename,
        "status": "EXTRACTION_FAILED",
        "skills": [],
        "total_years_experience": 0.0,
        "education": "Unknown",
        "projects": [],
        "classification": "Neither/Uncertain",
        "lca_score": 0,
        "lca_reasoning": reason,
        "ui_ux_score": 0,
        "ui_ux_reasoning": reason,
        "source_link": "#uploaded-live",
    }


# ==========================================
# 4. SYSTEM PROMPT & RUBRIC
# ==========================================
SYSTEM_PROMPT = """
You are an expert ATS (Applicant Tracking System) evaluator. Extract structured information from the resume text and score the candidate against two Job Descriptions (JDs) using the deterministic rubric below.

JD1: LifeCycle Assessment (LCA) Role (4-6 Years Experience Required)
- Rubric Breakdown (0-100):
  * Domain & Tool Expertise (0-45 pts): LCA, GHG accounting, carbon footprinting, SimaPro, GaBi, OpenLCA, Ecoinvent, ISO 14040/14044, sustainability consulting.
  * Experience Alignment (0-35 pts): 4-6 years relevant experience gets full points; 2-3.9 or 6.1-8 years gets partial points; <2 years gets low points.
  * Education & Relevant Projects (0-20 pts): Environmental engineering/science, chemical/process engineering, or lifecycle case studies.

JD2: UI/UX Design Internship Role (Entry-level / Intern)
- Rubric Breakdown (0-100):
  * Design Tools & Skills (0-45 pts): Figma, wireframing, prototyping, user research, usability testing, design systems, Adobe XD/Creative Suite.
  * Projects & Portfolio Evidence (0-40 pts): UI/UX case studies, app/web redesigns, interactive prototypes, portfolio links.
  * Experience & Education Fit (0-15 pts): Students, fresh graduates, or candidates with 0-2 years of design experience.

RULES:
1. Extract factual skills, total years of experience, education, and projects.
2. Score strictly. A pure UI/UX designer must receive near 0 for LCA, and a pure sustainability engineer must receive near 0 for UI/UX.
3. Classify as 'LCA' (if LCA >= 50 and UI/UX < 50), 'UI/UX' (if UI/UX >= 50 and LCA < 50), 'Both' (if both >= 50), or 'Neither/Uncertain' (if both < 50).
4. Provide 1-2 sentences of clear, human-readable evidence for each score.
"""


# ==========================================
# 5. API ENDPOINTS
# ==========================================
@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify Vercel serverless deployment."""
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    return {"status": "online", "openai_key_configured": has_key}


@app.post("/api/upload")
async def upload_and_evaluate_resume(file: UploadFile = File(...)):
    """
    Ingests an uploaded .docx or .pdf resume in memory, extracts text,
    evaluates against JD1 & JD2, cleans the output, and returns the candidate JSON.
    """
    filename = file.filename or "uploaded_resume"
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    # 1. Validate file extension
    if ext not in {"docx", "pdf"}:
        return build_error_response(
            filename,
            f"Unsupported file format '.{ext}'. Please upload a .docx or .pdf file (legacy binary .doc files are not supported in serverless memory).",
        )

    # 2. Read file bytes safely in memory
    try:
        file_bytes = await file.read()
    except Exception as e:
        return build_error_response(
            filename, f"Failed to read uploaded file stream: {str(e)}"
        )

    if not file_bytes:
        return build_error_response(filename, "Uploaded file is empty (0 bytes).")

    # Enforce 10MB limit to protect serverless memory
    if len(file_bytes) > 10 * 1024 * 1024:
        return build_error_response(filename, "File exceeds the 10MB size limit.")

    # 3. Extract text based on file extension
    try:
        if ext == "docx":
            extracted_text = extract_text_from_docx_bytes(file_bytes)
        else:
            extracted_text = extract_text_from_pdf_bytes(file_bytes)
    except Exception as e:
        return build_error_response(
            filename, f"Corrupted or unreadable {ext.upper()} structure: {str(e)}"
        )

    # Check if the file yielded meaningful text (catches blank files or image-only scanned PDFs)
    if not extracted_text or len(extracted_text.strip()) < 25:
        return build_error_response(
            filename,
            "No readable text layer found. The document appears to be blank, corrupted, or a scanned image without OCR text.",
        )

    # 4. Verify OpenAI API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is missing from server environment variables.",
        )

    # 5. Evaluate with OpenAI Structured Outputs
    try:
        client = OpenAI(api_key=api_key)
        # Truncate extreme outliers to 25,000 chars to keep latency well under Vercel's 10s timeout
        safe_text = extracted_text[:25000]

        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Filename: {filename}\n\nResume Text:\n{safe_text}",
                },
            ],
            response_format=CandidateEvaluation,
            temperature=0.0,  # Deterministic scoring
        )

        parsed_obj = completion.choices[0].message.parsed
        if not parsed_obj:
            return build_error_response(
                filename, "LLM refused or failed to generate structured output."
            )

        raw_dict = parsed_obj.model_dump()
        raw_dict["status"] = "SUCCESS"
        return clean_candidate_data(raw_dict, filename=filename)

    except Exception as e:
        return build_error_response(filename, f"AI Evaluation Error: {str(e)}")
