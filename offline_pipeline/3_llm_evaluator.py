import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from offline_pipeline.schema import CandidateEvaluation
from data.resume_links import RESUMES_LINKS
load_dotenv()

# The original Zoho view URLs to fulfill the "Preserve a link" requirement



# Initialize OpenAI Client
client = OpenAI()

SYSTEM_PROMPT = """
You are an expert ATS (Applicant Tracking System). Your job is to extract structured data from a raw resume and evaluate it against two specific Job Descriptions (JDs).

JD1: LifeCycle Assessment (LCA) Role
- Requires 4-6 years of experience.
- Key skills: LCA, carbon footprinting, environmental impact, SimaPro, GaBi, OpenLCA, ISO 14040/14044.

JD2: UI/UX Design Internship Role
- Entry-level / Intern role (0-2 years experience is fine).
- Key skills: Figma, wireframing, prototyping, user research, UI design, Adobe Creative Suite.

INSTRUCTIONS:
1. Extract skills, experience, education, and projects.
2. Score the resume for BOTH JD1 and JD2 from 0-100. Be strict. If someone is a pure designer, their LCA score should be 0.
3. Classify the candidate into: 'LCA', 'UI/UX', 'Both', or 'Neither/Uncertain'.
4. Provide a short, factual reasoning for each score citing explicit evidence from the text.
"""


def evaluate_single_resume(filename: str, raw_text: str, source_link: str) -> dict:
    """Evaluates a single resume text string using GPT-4o-mini and returns a clean dictionary."""

    # Handle the known error case gracefully without hitting the API
    if raw_text == "[EXTRACTION_FAILED]":
        return {
            "filename": filename,
            "status": "EXTRACTION_FAILED",
            "skills": [],
            "total_years_experience": 0.0,
            "education": "Unknown",
            "projects": [],
            "classification": "Neither/Uncertain",
            "lca_score": 0,
            "lca_reasoning": "File was unreadable or corrupted.",
            "ui_ux_score": 0,
            "ui_ux_reasoning": "File was unreadable or corrupted.",
            "source_link": source_link,
        }

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # or 5 mini
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Filename: {filename}\n\nResume Text:\n{raw_text}",
                },
            ],
            response_format=CandidateEvaluation,
        )

        # Pydantic automatically serializes this into a validated dictionary
        result = completion.choices[0].message.parsed.model_dump()
        result["source_link"] = source_link
        return result

    except Exception as e:
        print(f"❌ API Error on {filename}: {e}")
        return {
            "filename": filename,
            "status": "EXTRACTION_FAILED",
            "skills": [],
            "total_years_experience": 0.0,
            "education": "Unknown",
            "projects": [],
            "classification": "Neither/Uncertain",
            "lca_score": 0,
            "lca_reasoning": f"API Evaluation Failed: {str(e)}",
            "ui_ux_score": 0,
            "ui_ux_reasoning": f"API Evaluation Failed: {str(e)}",
            "source_link": source_link,
        }


def run_llm_evaluation():
    input_file = os.path.join("offline_pipeline", "parsed_texts.json")

    # Ensure the frontend data folder exists
    os.makedirs(os.path.join("src", "data"), exist_ok=True)
    output_file = os.path.join("src", "data", "candidates.json")

    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        parsed_data = json.load(f)

    evaluated_candidates = []
    total = len(parsed_data)

    print(f"🧠 Initiating LLM Evaluation for {total} candidates...")

    for idx, (filename, text) in enumerate(parsed_data.items(), 1):
        print(f"[{idx}/{total}] Evaluating {filename}...")
        link = RESUMES_LINKS.get(filename, "")

        eval_result = evaluate_single_resume(filename, text, link)
        evaluated_candidates.append(eval_result)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(evaluated_candidates, f, indent=4)

    print("\n--- 🏁 LLM Evaluation Complete ---")
    print(f"💾 Saved strictly structured JSON to {output_file}")


if __name__ == "__main__":
    run_llm_evaluation()
