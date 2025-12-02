"""Pipeline orchestrator for complete provenance checking pipeline."""
from pathlib import Path
from typing import Dict, List, Optional
import logging
import numpy as np
import json
from datetime import datetime

from src.stage2_preprocessing import Segmenter, StemSeparator
from src.stage3_embedding import EmbeddingGenerator
from src.stage4_indexing import FAISSIndexer
from src.stage5_classifier import AIDetector
from src.stage6_reporting import ProvenanceReportBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the complete provenance checking pipeline."""
    
    def __init__(
        self,
        segment_length: float = 0.5,
        sample_rate: int = 44100,
        embedding_dim: int = 512,
        index_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
        classifier_paths: Optional[Dict[str, Path]] = None,
        model_hash: Optional[str] = None,
        index_hash: Optional[str] = None
    ):
        """
        Initialize pipeline orchestrator.
        
        Args:
            segment_length: Segment length in seconds (default: 0.5)
            sample_rate: Sample rate (default: 44100)
            embedding_dim: Embedding dimension (default: 512)
            index_path: Path to FAISS index
            metadata_path: Path to index metadata
            classifier_paths: Dict mapping stem_type -> classifier path
            model_hash: Hash of embedding model
            index_hash: Hash of FAISS index
        """
        self.segment_length = segment_length
        self.sample_rate = sample_rate
        self.embedding_dim = embedding_dim
        
        # Initialize components
        self.segmenter = Segmenter(
            segment_length=segment_length,
            sample_rate=sample_rate
        )
        self.stem_separator = StemSeparator(sample_rate=sample_rate)
        self.embedder = EmbeddingGenerator(
            embedding_dim=embedding_dim,
            sample_rate=sample_rate
        )
        
        # Load FAISS index
        self.indexer = FAISSIndexer(embedding_dim=embedding_dim)
        if index_path and index_path.exists() and metadata_path and metadata_path.exists():
            try:
                self.indexer.load_index(index_path, metadata_path)
                logger.info(f"Loaded FAISS index from {index_path}")
            except Exception as e:
                logger.warning(f"Failed to load index: {e}. Will create new index.")
        
        # Load classifiers
        self.classifiers = {}
        if classifier_paths:
            for stem_type, path in classifier_paths.items():
                if path and path.exists():
                    try:
                        detector = AIDetector(model_path=path, stem_type=stem_type)
                        self.classifiers[stem_type] = detector
                        logger.info(f"Loaded classifier for {stem_type} from {path}")
                    except Exception as e:
                        logger.warning(f"Failed to load classifier for {stem_type}: {e}")
        
        # Report builder
        self.report_builder = ProvenanceReportBuilder(
            model_hash=model_hash,
            index_hash=index_hash
        )
    
    def process_file(
        self,
        input_path: Path,
        output_dir: Optional[Path] = None,
        stems_to_process: Optional[List[str]] = None
    ) -> Dict:
        """
        Process a single audio file through the complete pipeline.
        
        Args:
            input_path: Path to input audio file
            output_dir: Directory for intermediate outputs (optional)
            stems_to_process: List of stems to process (default: all)
        
        Returns:
            Complete provenance report dictionary
        """
        logger.info(f"Processing file: {input_path}")
        
        if output_dir is None:
            output_dir = Path("data/processing") / input_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if stems_to_process is None:
            stems_to_process = ["vocals", "drums", "bass", "other"]
        
        file_id = input_path.stem
        
        # Step 1: Segment audio
        logger.info("Step 1: Segmenting audio...")
        segments_dir = output_dir / "segments"
        segments = self.segmenter.segment_file(input_path, segments_dir)
        logger.info(f"Created {len(segments)} segments")
        
        # Step 2: Process each segment with stem separation
        logger.info("Step 2: Separating stems and generating embeddings...")
        all_segment_metadata = []
        all_embeddings = []
        matches = {}  # segment_id -> list of matches
        classifier_scores = {}  # segment_id -> {stem_type: prob}
        
        for seg in segments:
            segment_id = seg["segment_id"]
            segment_path = Path(seg["path"])
            
            # Load segment audio
            import soundfile as sf
            segment_audio, sr = sf.read(segment_path)
            
            # Separate into stems
            stems_dict = self.stem_separator.separate_segment(
                segment_audio, sr, stems=stems_to_process
            )
            
            # Process each stem
            for stem_type, stem_audio in stems_dict.items():
                # Save stem segment temporarily
                stem_seg_path = output_dir / "stem_segments" / f"{segment_id}_{stem_type}.wav"
                stem_seg_path.parent.mkdir(parents=True, exist_ok=True)
                sf.write(str(stem_seg_path), stem_audio, self.sample_rate)
                
                # Generate embedding for stem
                emb = self.embedder.generate_embedding(stem_seg_path)
                
                # Search for matches
                search_results = self.indexer.search(emb, k=10, threshold=0.7)
                matches[f"{segment_id}_{stem_type}"] = search_results
                
                # Classify (if classifier available)
                if stem_type in self.classifiers:
                    _, prob = self.classifiers[stem_type].predict(emb, return_proba=True)
                    if segment_id not in classifier_scores:
                        classifier_scores[segment_id] = {}
                    classifier_scores[segment_id][stem_type] = float(prob[0] if isinstance(prob, np.ndarray) else prob)
                else:
                    # Default probability if no classifier
                    if segment_id not in classifier_scores:
                        classifier_scores[segment_id] = {}
                    classifier_scores[segment_id][stem_type] = 0.5
                
                # Store metadata
                stem_seg_meta = seg.copy()
                stem_seg_meta["stem_type"] = stem_type
                stem_seg_meta["segment_id"] = f"{segment_id}_{stem_type}"
                stem_seg_meta["path"] = str(stem_seg_path)
                all_segment_metadata.append(stem_seg_meta)
                all_embeddings.append(emb)
        
        # Step 3: Build provenance report
        logger.info("Step 3: Building provenance report...")
        
        # Group segments by original segment_id for report
        report_segments = []
        for seg in segments:
            seg_id = seg["segment_id"]
            # Get classifier scores for all stems of this segment
            seg_scores = classifier_scores.get(seg_id, {})
            # Get matches for all stems
            seg_matches = []
            for stem_type in stems_to_process:
                stem_matches = matches.get(f"{seg_id}_{stem_type}", [])
                seg_matches.extend(stem_matches)
            # Sort by similarity
            seg_matches.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            
            # Use the stem with highest AI probability for segment-level classification
            max_ai_prob = max(seg_scores.values()) if seg_scores else 0.0
            dominant_stem = max(seg_scores.items(), key=lambda x: x[1])[0] if seg_scores else "mix"
            
            report_seg = seg.copy()
            report_seg["stem_type"] = dominant_stem
            report_seg["all_stem_scores"] = seg_scores
            report_segments.append(report_seg)
        
        # Build report
        report = self.report_builder.build_report(
            file_id=file_id,
            segments=report_segments,
            matches={seg["segment_id"]: matches.get(f"{seg['segment_id']}_{seg.get('stem_type', 'mix')}", []) 
                    for seg in report_segments},
            classifier_scores=classifier_scores,
            metadata={
                "input_file": str(input_path),
                "processing_timestamp": datetime.utcnow().isoformat(),
                "stems_processed": stems_to_process
            }
        )
        
        logger.info(f"Completed processing. Report summary: {report['summary']}")
        return report

