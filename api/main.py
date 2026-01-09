"""FastAPI server for provenance checking API."""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging
from pathlib import Path
import uuid
import json
import traceback

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
    EMBEDDING_DIM,
    EMBEDDING_MODEL_TYPE,
    MERT_MODEL_NAME
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

# Web UI templates and static files
# Use absolute paths to ensure files are found
base_dir = Path(__file__).parent.parent
templates_dir = base_dir / "web_ui" / "templates"
static_dir = base_dir / "web_ui" / "static"

logger.info(f"Templates directory: {templates_dir} (exists: {templates_dir.exists()})")
logger.info(f"Static directory: {static_dir} (exists: {static_dir.exists()})")

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

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
# For MERT, we use the model identifier since it's loaded from Hugging Face, not a local file
if EMBEDDING_MODEL_PATH and EMBEDDING_MODEL_PATH.exists():
    model_hash = calculate_file_hash(EMBEDDING_MODEL_PATH)
elif EMBEDDING_MODEL_TYPE == "mert":
    # Calculate hash from MERT model identifier for provenance tracking
    import hashlib
    model_identifier = f"{EMBEDDING_MODEL_TYPE}:{MERT_MODEL_NAME}"
    model_hash = hashlib.sha256(model_identifier.encode()).hexdigest()[:16]
    logger.info(f"Using MERT model identifier for hash: {MERT_MODEL_NAME}")
    logger.info(f"Model checksum (from identifier): {model_hash}")
else:
    model_hash = None

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


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main web UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api", response_class=HTMLResponse)
async def api_root(request: Request):
    """API info endpoint - redirect to web UI."""
    return templates.TemplateResponse("index.html", {"request": request})


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
        logger.info(f"📤 Receiving upload for job {job_id}")
        logger.info(f"   Filename: {file.filename}")
        logger.info(f"   Content type: {file.content_type}")
        logger.info(f"   Upload directory: {upload_dir}")
        logger.info(f"   Target path: {file_path}")
        
        # Ensure upload directory exists
        upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"   Upload directory exists: {upload_dir.exists()}")
        
        # Read and save file
        logger.info(f"   Reading file content...")
        content = await file.read()
        logger.info(f"   Read {len(content)} bytes")
        
        logger.info(f"   Writing to {file_path}...")
        with open(file_path, "wb") as f:
            f.write(content)
        
        file_size = file_path.stat().st_size
        logger.info(f"✅ File saved: {file_path} ({file_size} bytes)")
        logger.info(f"   File exists: {file_path.exists()}")
        
        # Initialize job
        from datetime import datetime
        jobs[job_id] = {
            "status": "processing",
            "file_path": str(file_path),
            "created_at": datetime.utcnow().isoformat(),
            "current_stage": "uploading",
            "progress_percent": 0,
            "stage_message": "File uploaded, starting processing..."
        }
        logger.info(f"   Job initialized: {jobs[job_id]}")
        
        # Process in background
        logger.info(f"🔄 Adding background task for job {job_id}")
        logger.info(f"   Background task will process: {file_path}")
        
        # Use background_tasks to process asynchronously
        background_tasks.add_task(process_provenance, job_id, file_path)
        
        logger.info(f"✅ Background task added successfully for job {job_id}")
        
        response = ProvenanceResponse(
            job_id=job_id,
            status="processing",
            message="Provenance check started"
        )
        logger.info(f"📤 Returning response: {response}")
        return response
    
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"❌ Error uploading file: {e}")
        logger.error(f"   Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


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
    
    # Return JSON directly for web UI
    with open(report_path, 'r') as f:
        report_data = json.load(f)
    return JSONResponse(content=report_data)


def process_provenance(job_id: str, file_path: Path):
    """Background task to process provenance check."""
    try:
        logger.info(f"🚀 Starting background processing for job {job_id}")
        logger.info(f"   File path: {file_path}")
        logger.info(f"   File path type: {type(file_path)}")
        logger.info(f"   File path exists: {file_path.exists()}")
        
        # Convert to Path if it's a string
        if isinstance(file_path, str):
            file_path = Path(file_path)
            logger.info(f"   Converted string to Path: {file_path}")
        
        if not file_path.exists():
            error_msg = f"Uploaded file not found: {file_path}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"   Current working directory: {Path.cwd()}")
            logger.error(f"   Absolute path: {file_path.absolute()}")
            raise FileNotFoundError(error_msg)
        
        logger.info(f"   File size: {file_path.stat().st_size} bytes")
        
        # Run pipeline with progress tracking
        logger.info(f"🔄 Starting pipeline processing for {file_path.name}")
        logger.info(f"   Orchestrator initialized: {orchestrator is not None}")
        
        # Create a progress callback function
        def update_progress(stage: str, percent: int, message: str):
            if job_id in jobs:
                jobs[job_id]["current_stage"] = stage
                jobs[job_id]["progress_percent"] = percent
                jobs[job_id]["stage_message"] = message
                logger.info(f"📊 Progress update for job {job_id}: {stage} ({percent}%) - {message}")
        
        # Process with progress callback
        report = orchestrator.process_file(file_path, progress_callback=update_progress)
        
        # Update progress to 100% when complete
        if job_id in jobs:
            jobs[job_id]["current_stage"] = "completed"
            jobs[job_id]["progress_percent"] = 100
            jobs[job_id]["stage_message"] = "Processing complete!"
        logger.info(f"✅ Pipeline processing completed for job {job_id}")
        logger.info(f"   Report keys: {list(report.keys()) if isinstance(report, dict) else 'Not a dict'}")
        
        # Save report
        report_dir = Path("data/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"report_{job_id}.json"
        
        logger.info(f"💾 Saving report to {report_path}")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"   Report saved: {report_path.exists()}")
        
        # Update job status
        if job_id in jobs:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["report_path"] = str(report_path)
            jobs[job_id]["current_stage"] = "completed"
            jobs[job_id]["progress_percent"] = 100
            jobs[job_id]["stage_message"] = "Processing complete!"
            logger.info(f"✅ Job status updated to completed")
        else:
            logger.warning(f"⚠️ Job {job_id} not found in jobs dict")
        
        logger.info(f"✅ Completed provenance check for job {job_id}")
        logger.info(f"   Report saved to: {report_path}")
    
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"❌ Error processing job {job_id}: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Traceback: {error_trace}")
        
        if job_id in jobs:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)
            jobs[job_id]["error_trace"] = error_trace
        else:
            logger.error(f"❌ Cannot update job status - job {job_id} not found in jobs dict")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "orchestrator_initialized": orchestrator is not None,
        "jobs_count": len(jobs)
    }


@app.get("/api/v1/index-status")
async def get_index_status():
    """Get FAISS index status and statistics."""
    index_stats = orchestrator.indexer.get_stats()
    return {
        "index_loaded": index_stats.get("index_type", "None") != "None",
        "index_type": index_stats.get("index_type", "None"),
        "total_vectors": index_stats.get("total_vectors", 0),
        "embedding_dim": index_stats.get("embedding_dim", 512),
        "index_path": str(FAISS_INDEX_PATH),
        "index_exists": FAISS_INDEX_PATH.exists(),
        "metadata_exists": FAISS_METADATA_PATH.exists()
    }
