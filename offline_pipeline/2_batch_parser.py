import os
import json
import docx
from pypdf import PdfReader
from io import BytesIO
from typing import Union, Dict

def extract_text_from_docx(file_source: Union[str, BytesIO]) -> str:
    """
    Extracts text from a DOCX file, including standard paragraphs and tables.
    Accepts a file path (str) or an in-memory byte stream (BytesIO).
    """
    try:
        doc = docx.Document(file_source)
        full_text = []
        
        # 1. Extract standard paragraph text
        for para in doc.paragraphs:
            clean_text = para.text.strip()
            if clean_text:
                full_text.append(clean_text)
                
        # 2. Extract table data (often missed, but crucial for resumes)
        for table in doc.tables:
            for row in table.rows:
                # Deduplicate cells (merged cells repeat text in python-docx)
                seen_cells = set()
                row_data = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text and cell_text not in seen_cells:
                        seen_cells.add(cell_text)
                        row_data.append(cell_text)
                if row_data:
                    full_text.append(" | ".join(row_data))
                    
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error parsing DOCX: {e}")
        return ""


def extract_text_from_pdf(file_source: Union[str, BytesIO]) -> str:
    """
    Extracts text from a PDF file.
    Accepts a file path (str) or an in-memory byte stream (BytesIO).
    """
    try:
        reader = PdfReader(file_source)
        full_text = []
        
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text.append(page_text.strip())
                
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""


def parse_resume(file_source: Union[str, BytesIO], filename: str) -> str:
    """Routing function to determine the correct parser based on file extension."""
    ext = filename.lower().split('.')[-1]
    
    if ext == "docx":
        return extract_text_from_docx(file_source)
    elif ext == "pdf":
        return extract_text_from_pdf(file_source)
    else:
        print(f"Unsupported file extension: {ext} for {filename}")
        return ""


def run_batch_parsing():
    """
    Iterates through the local downloaded resumes, extracts their text, 
    and saves the raw strings into a single JSON file for the LLM step.
    """
    input_dir = os.path.join("offline_pipeline", "raw_resumes")
    output_file = os.path.join("offline_pipeline", "parsed_texts.json")
    
    if not os.path.exists(input_dir):
        print(f"❌ Input directory not found: {input_dir}")
        return

    parsed_data: Dict[str, str] = {}
    success_count = 0
    empty_count = 0

    print("🚀 Starting Batch Parsing...")
    
    for filename in os.listdir(input_dir):
        file_path = os.path.join(input_dir, filename)
        
        # Skip directories if any
        if not os.path.isfile(file_path):
            continue
            
        print(f"📄 Parsing: {filename}...")
        extracted_text = parse_resume(file_path, filename)
        
        if extracted_text.strip():
            parsed_data[filename] = extracted_text
            success_count += 1
        else:
            print(f"⚠️ Warning: No text extracted from {filename}")
            # Keep track of failed extractions to satisfy the prototype's error handling requirements
            parsed_data[filename] = "[EXTRACTION_FAILED]"
            empty_count += 1

    # Save to a JSON payload for step 3
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=4)

    print("\n--- 🏁 Parsing Complete ---")
    print(f"Successfully parsed: {success_count}")
    print(f"Failed/Empty: {empty_count}")
    print(f"💾 Saved raw text mappings to {output_file}")


if __name__ == "__main__":
    run_batch_parsing()