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
from src.stage6_reporting.report_builder import ProvenanceReportBuilder
from config.settings import (
    FAISS_INDEX_PATH,
    FAISS_METADATA_PATH,
    CLASSIFIER_PATHS,
    EMBEDDING_MODEL_PATH,
    SEGMENT_LENGTH,
    SAMPLE_RATE,
    EMBEDDING_DIM
)

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

# Calculate hashes for provenance tracking
def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    if not file_path.exists():
        return "unknown"
    import hashlib
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()[:16]

# Initialize orchestrator with index and classifiers
logger.info("Initializing pipeline orchestrator...")
logger.info(f"Index path: {FAISS_INDEX_PATH}")
logger.info(f"Index exists: {FAISS_INDEX_PATH.exists()}")
logger.info(f"Metadata exists: {FAISS_METADATA_PATH.exists()}")

# Calculate model and index hashes for provenance
model_hash = calculate_file_hash(EMBEDDING_MODEL_PATH) if EMBEDDING_MODEL_PATH else None
index_hash = calculate_file_hash(FAISS_INDEX_PATH) if FAISS_INDEX_PATH.exists() else None

orchestrator = PipelineOrchestrator(
    segment_length=SEGMENT_LENGTH,
    sample_rate=SAMPLE_RATE,
    embedding_dim=EMBEDDING_DIM,
    index_path=FAISS_INDEX_PATH if FAISS_INDEX_PATH.exists() else None,
    metadata_path=FAISS_METADATA_PATH if FAISS_METADATA_PATH.exists() else None,
    classifier_paths=CLASSIFIER_PATHS,
    model_hash=model_hash,
    index_hash=index_hash
)

# Log index status
index_stats = orchestrator.indexer.get_stats()
logger.info(f"Index status: {index_stats}")
if index_stats.get("total_vectors", 0) == 0:
    logger.warning("⚠️ FAISS index is empty or not loaded. Similarity search will not work.")
    logger.warning("   To build an index, run: python scripts/build_index.py --embeddings_dir data/embeddings")
else:
    logger.info(f"✅ FAISS index loaded: {index_stats.get('total_vectors')} vectors, type: {index_stats.get('index_type')}")
    logger.info(f"   Index hash: {index_hash}")


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