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
from src.utils.performance_tracker import PerformanceTracker

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
        self._index_loaded = False
        
        if index_path and metadata_path:
            # Check if files exist
            index_exists = index_path.exists()
            metadata_exists = metadata_path.exists()
            
            logger.info(f"Checking index files:")
            logger.info(f"   Index path: {index_path}")
            logger.info(f"   Index exists: {index_exists}")
            logger.info(f"   Metadata path: {metadata_path}")
            logger.info(f"   Metadata exists: {metadata_exists}")
            
            if index_exists and metadata_exists:
                try:
                    self.indexer.load_index(index_path, metadata_path)
                    stats = self.indexer.get_stats()
                    self._index_loaded = True
                    logger.info(f"✅ FAISS index successfully loaded!")
                    logger.info(f"   Index type: {stats.get('index_type')}")
                    logger.info(f"   Total vectors: {stats.get('total_vectors')}")
                    logger.info(f"   Embedding dim: {stats.get('embedding_dim')}")
                except Exception as e:
                    logger.error(f"❌ Failed to load index: {e}")
                    logger.error(f"   Error type: {type(e).__name__}")
                    import traceback
                    logger.error(f"   Traceback: {traceback.format_exc()}")
                    logger.warning("   Similarity search will not work without a loaded index.")
                    self._index_loaded = False
            else:
                if not index_exists:
                    logger.warning(f"⚠️ Index file not found: {index_path}")
                if not metadata_exists:
                    logger.warning(f"⚠️ Metadata file not found: {metadata_path}")
                logger.warning("⚠️ FAISS index not loaded. Similarity search will not work.")
                logger.warning("   To build an index, run: python scripts/build_index.py --embeddings_dir data/embeddings")
        else:
            logger.warning("⚠️ Index paths not provided. Similarity search will not work.")
        
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
        
        # Performance tracker
        self.performance_tracker = PerformanceTracker()
    
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
        import time
        
        # Start performance tracking
        self.performance_tracker.start()
        
        logger.info(f"Processing file: {input_path}")
        
        if output_dir is None:
            output_dir = Path("data/processing") / input_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if stems_to_process is None:
            stems_to_process = ["vocals", "drums", "bass", "other"]
        
        file_id = input_path.stem
        
        # Set processing start time for report builder
        self.report_builder.processing_start_time = datetime.utcnow()
        
        # Step 1: Segment audio
        logger.info("Step 1: Segmenting audio...")
        seg_start = time.time()
        segments_dir = output_dir / "segments"
        segments = self.segmenter.segment_file(input_path, segments_dir)
        seg_duration = time.time() - seg_start
        self.performance_tracker.record_stage("segmentation", seg_duration)
        logger.info(f"Created {len(segments)} segments")
        
        # Get file duration
        import soundfile as sf
        audio_info = sf.info(input_path)
        duration_sec = audio_info.duration
        
        # Step 2: Process each segment with stem separation
        logger.info("Step 2: Separating stems and generating embeddings...")
        all_segment_metadata = []
        all_embeddings = []
        matches = {}  # segment_id -> list of matches
        classifier_scores = {}  # segment_id -> {stem_type: prob}
        consecutive_matches = {}  # segment_id -> consecutive match count
        
        # Track consecutive matches by source file
        source_match_tracker = {}  # source_file_id -> [list of consecutive segment_ids]
        
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
                emb_start = time.time()
                emb = self.embedder.generate_embedding(stem_seg_path)
                emb_duration = time.time() - emb_start
                self.performance_tracker.record_embedding_time(emb_duration)
                
                # Search for matches
                search_start = time.time()
                if self._index_loaded and self.indexer.index is not None and self.indexer.index.ntotal > 0:
                    # Use lower threshold (0.5) to catch more potential matches
                    search_results = self.indexer.search(emb, k=10, threshold=0.5)
                    if search_results:
                        logger.debug(f"Found {len(search_results)} matches for {segment_id}_{stem_type}")
                    else:
                        logger.debug(f"No matches above threshold for {segment_id}_{stem_type} (index has {self.indexer.index.ntotal} vectors)")
                else:
                    # Index not loaded, return empty results
                    search_results = []
                    if not self._index_loaded:
                        logger.warning(f"⚠️ Index not loaded - skipping similarity search for {segment_id}_{stem_type}")
                
                search_duration = time.time() - search_start
                self.performance_tracker.record_search_time(search_duration)
                matches[f"{segment_id}_{stem_type}"] = search_results
                
                # Track consecutive matches for fusion formula
                if search_results:
                    top_match = search_results[0]
                    source_file = top_match.get("file_id")
                    if source_file:
                        # Initialize tracker for this source if needed
                        if source_file not in source_match_tracker:
                            source_match_tracker[source_file] = []
                        source_match_tracker[source_file].append(segment_id)
                
                # Classify (if classifier available)
                class_start = time.time()
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
                class_duration = time.time() - class_start
                self.performance_tracker.record_classification_time(class_duration)
                
                # Store metadata
                stem_seg_meta = seg.copy()
                stem_seg_meta["stem_type"] = stem_type
                stem_seg_meta["segment_id"] = f"{segment_id}_{stem_type}"
                stem_seg_meta["path"] = str(stem_seg_path)
                all_segment_metadata.append(stem_seg_meta)
                all_embeddings.append(emb)
        
        # Calculate consecutive matches for each segment
        # Count how many consecutive segments match the same source
        for source_file, matched_segments in source_match_tracker.items():
            # Sort segments by index to find consecutive sequences
            seg_indices = {}
            for seg in segments:
                seg_indices[seg["segment_id"]] = seg.get("index", 0)
            
            # Find consecutive sequences
            matched_segments_sorted = sorted(
                matched_segments,
                key=lambda sid: seg_indices.get(sid, 0)
            )
            
            current_sequence = []
            for seg_id in matched_segments_sorted:
                if not current_sequence:
                    current_sequence = [seg_id]
                else:
                    # Check if this segment is consecutive to the last one
                    last_idx = seg_indices.get(current_sequence[-1], 0)
                    curr_idx = seg_indices.get(seg_id, 0)
                    if curr_idx == last_idx + 1:
                        current_sequence.append(seg_id)
                    else:
                        # End of sequence, update consecutive counts
                        n_cons = len(current_sequence)
                        for seq_seg_id in current_sequence:
                            consecutive_matches[seq_seg_id] = max(
                                consecutive_matches.get(seq_seg_id, 0),
                                n_cons
                            )
                        current_sequence = [seg_id]
            
            # Handle last sequence
            if current_sequence:
                n_cons = len(current_sequence)
                for seq_seg_id in current_sequence:
                    consecutive_matches[seq_seg_id] = max(
                        consecutive_matches.get(seq_seg_id, 0),
                        n_cons
                    )
        
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
        
        # Get model and index info
        model_info = self.embedder.get_model_info() if hasattr(self.embedder, 'get_model_info') else {}
        index_stats = self.indexer.get_stats() if hasattr(self.indexer, 'get_stats') else {}
        
        # Build report
        report = self.report_builder.build_report(
            file_id=file_id,
            segments=report_segments,
            matches={seg["segment_id"]: matches.get(f"{seg['segment_id']}_{seg.get('stem_type', 'mix')}", []) 
                    for seg in report_segments},
            classifier_scores=classifier_scores,
            consecutive_matches=consecutive_matches,
            original_file_path=input_path,
            output_dir=output_dir,
            metadata={
                "input_file": str(input_path),
                "original_filename": input_path.name,
                "duration_sec": duration_sec,
                "processing_timestamp": datetime.utcnow().isoformat(),
                "stems_processed": stems_to_process,
                "model_type": model_info.get("active_model", "unknown"),
                "index_type": index_stats.get("index_type", "unknown"),
                "index_size": index_stats.get("total_vectors", 0),
                "augmentation_profile": "default"
            }
        )
        
        # End performance tracking
        self.performance_tracker.end()
        
        # Generate performance report
        perf_report_path = output_dir / "perf_report.json"
        try:
            perf_report = self.performance_tracker.generate_report(
                perf_report_path,
                target_latency=1.0,
                target_throughput=10.0,
                target_embedding_ms=50.0
            )
            logger.info(f"Performance report saved to {perf_report_path}")
        except Exception as e:
            logger.warning(f"Failed to generate performance report: {e}")
        
        logger.info(f"Completed processing. Report summary: {report.get('overall_summary', {})}")
        return report

