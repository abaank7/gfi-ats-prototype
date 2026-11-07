from pydantic import BaseModel, Field
from typing import List, Literal

class CandidateEvaluation(BaseModel):
    filename: str = Field(description="The original filename")
    status: Literal["SUCCESS", "EXTRACTION_FAILED"] = Field(
        description="Must be 'SUCCESS' or 'EXTRACTION_FAILED'"
    )
    skills: List[str] = Field(description="List of core professional skills extracted from the resume")
    total_years_experience: float = Field(
        description="Total cumulative years of relevant professional experience. Put 0.0 if intern/fresher."
    )
    education: str = Field(description="Highest degree, major, and institution if available")
    projects: List[str] = Field(description="Concise titles or 1-line summaries of key relevant projects")
    
    classification: Literal["LCA", "UI/UX", "Both", "Neither/Uncertain"] = Field(
        description="Must be exactly one of: 'LCA', 'UI/UX', 'Both', 'Neither/Uncertain'"
    )
    
    lca_score: int = Field(
        description="Match score 0-100 for the LifeCycle Assessment (LCA) role (4-6 years exp)."
    )
    lca_reasoning: str = Field(
        description="1-2 concise sentences citing explicit evidence from the resume for the LCA score."
    )
    
    ui_ux_score: int = Field(
        description="Match score 0-100 for the UI/UX Design Internship role."
    )
    ui_ux_reasoning: str = Field(
        description="1-2 concise sentences citing explicit evidence from the resume for the UI/UX score."
    )
    
    source_link: str = Field(description="URL or reference marker to the source resume")