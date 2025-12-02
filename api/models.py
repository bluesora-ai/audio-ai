"""Pydantic models for API."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class ProvenanceRequest(BaseModel):
    """Request model for provenance check."""
    prompt: Optional[str] = None
    include_vocals: bool = True
    include_drums: bool = True
    include_bass: bool = True
    include_other: bool = True


class ProvenanceResponse(BaseModel):
    """Response model for provenance check initiation."""
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    """Job status model."""
    status: str  # processing, completed, failed
    file_path: Optional[str] = None
    report_path: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[str] = None