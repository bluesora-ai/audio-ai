"""FastAPI server for provenance checking API."""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging
from pathlib import Path
import uuid
import json

from api.models import ProvenanceRequest, ProvenanceResponse, JobStatus
from src.pipeline.rochestrator import PipelineOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audio Provenance API",
    description="API for checking audio provenance and detecting AI-generated content",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
jobs: Dict[str, Dict] = {}
orchestrator = PipelineOrchestrator()


@app.post("/api/v1/provenance-check", response_model=ProvenanceResponse)
async def provenance_check(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    prompt: Optional[str] = None
):
    """
    Check provenance of uploaded audio file.
    
    Returns job_id for async processing.
    """
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"{job_id}_{file.filename}"
    
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Initialize job
        from datetime import datetime
        jobs[job_id] = {
            "status": "processing",
            "file_path": str(file_path),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Process in background
        background_tasks.add_task(process_provenance, job_id, file_path)
        
        return ProvenanceResponse(
            job_id=job_id,
            status="processing",
            message="Provenance check started"
        )
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    """Get status of provenance check job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]


@app.get("/api/v1/reports/{job_id}")
async def get_report(job_id: str):
    """Get provenance report for completed job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    report_path = Path(job.get("report_path"))
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        report_path,
        media_type="application/json",
        filename=f"provenance_report_{job_id}.json"
    )


async def process_provenance(job_id: str, file_path: Path):
    """Background task to process provenance check."""
    try:
        logger.info(f"Processing provenance for job {job_id}")
        
        # Run pipeline
        report = orchestrator.process_file(file_path)
        
        # Save report
        report_dir = Path("data/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"report_{job_id}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["report_path"] = str(report_path)
        
        logger.info(f"Completed provenance check for job {job_id}")
    
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Audio Provenance API v2.0", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}