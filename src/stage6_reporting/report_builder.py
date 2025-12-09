"""Provenance report builder for Milestone 2."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib
import logging
import numpy as np
import soundfile as sf
import librosa
import subprocess
import sys

# Initialize logger first
logger = logging.getLogger(__name__)

# Try to import matplotlib (handle PIL/Pillow conflicts)
HAS_MATPLOTLIB = False
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except (ImportError, OSError, AttributeError) as e:
    HAS_MATPLOTLIB = False
    logger.warning(f"matplotlib not available: {e}. Spectrograms will not be generated.")


class ProvenanceReportBuilder:
    """Builds provenance reports with matches, classifier scores, and metadata."""
    
    def __init__(
        self,
        model_hash: Optional[str] = None,
        index_hash: Optional[str] = None,
        pipeline_version: Optional[str] = None,
        fusion_alpha: float = 0.6,
        fusion_beta: float = 0.3,
        fusion_gamma: float = 0.1,
        fusion_k: int = 2
    ):
        """
        Initialize report builder.
        
        Args:
            model_hash: Hash of embedding model
            index_hash: Hash of FAISS index
            pipeline_version: Git commit hash or version string
            fusion_alpha: Weight for classifier probability (default: 0.6)
            fusion_beta: Weight for similarity score (default: 0.3)
            fusion_gamma: Weight for consecutive matches (default: 0.1)
            fusion_k: Threshold for consecutive matches (default: 2)
        """
        self.model_hash = model_hash
        self.index_hash = index_hash
        self.pipeline_version = pipeline_version or self._get_git_version()
        self.fusion_alpha = fusion_alpha
        self.fusion_beta = fusion_beta
        self.fusion_gamma = fusion_gamma
        self.fusion_k = fusion_k
        self.timestamp = datetime.utcnow().isoformat()
        self.processing_start_time = None
    
    def _get_git_version(self) -> str:
        """Get git commit hash for pipeline version."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            if result.returncode == 0:
                return result.stdout.strip()[:16]  # First 16 chars
        except Exception:
            pass
        return "unknown"
    
    def build_report(
        self,
        file_id: str,
        segments: List[Dict],
        matches: Dict[str, List[Dict]],  # segment_id -> list of matches
        classifier_scores: Dict[str, Dict],  # segment_id -> {stem_type: prob}
        metadata: Optional[Dict] = None,
        original_file_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        consecutive_matches: Optional[Dict[str, int]] = None  # segment_id -> n_cons
    ) -> Dict:
        """
        Build complete provenance report.
        
        Args:
            file_id: Original file identifier
            segments: List of segment metadata
            matches: Dictionary of matches per segment
            classifier_scores: Dictionary of classifier scores per segment/stem
            metadata: Additional metadata
            original_file_path: Path to original audio file
            output_dir: Directory for evidence files
            consecutive_matches: Dictionary mapping segment_id -> consecutive match count
        
        Returns:
            Complete provenance report dictionary
        """
        if self.processing_start_time is None:
            self.processing_start_time = datetime.utcnow()
        
        processing_time = (datetime.utcnow() - self.processing_start_time).total_seconds()
        
        # Get model info from embedder if available
        model_type = "unknown"
        try:
            from src.stage3_embedding import EmbeddingGenerator
            # This is a placeholder - actual model type should be passed in metadata
            model_type = metadata.get("model_type", "mert") if metadata else "mert"
        except:
            pass
        
        report = {
            "job_id": metadata.get("job_id") if metadata else None,
            "file_id": file_id,
            "original_filename": metadata.get("original_filename") if metadata else file_id,
            "duration_sec": metadata.get("duration_sec") if metadata else None,
            "sample_rate": 44100,
            "created_at": self.timestamp,
            "pipeline_version": self.pipeline_version,
            "model_provenance": {
                "fingerprint_model": model_type,
                "fingerprint_model_checksum": self.model_hash or "unknown",
                "classifier_model": "RandomForest (per-stem)",
                "index_config": {
                    "index_type": metadata.get("index_type", "unknown") if metadata else "unknown",
                    "total_vectors": metadata.get("index_size", 0) if metadata else 0
                },
                "augmentation_profile": metadata.get("augmentation_profile", "default") if metadata else "default",
                "embedding_dim": 512,
                "model_type": model_type
            },
            "segments": [],
            "stems_summary": [],
            "overall_summary": {},
            "audit": {
                "processing_time_sec": processing_time,
                "logs_path": str(output_dir / "processing.log") if output_dir else None
            }
        }
        
        segments_flagged = 0
        segments_with_matches = 0
        
        # Track per-stem statistics
        stem_stats = {}  # stem_type -> {count, ai_count, matches_count, total_ai_prob}
        
        # Process each segment
        for seg in segments:
            segment_id = seg["segment_id"]
            stem_type = seg.get("stem_type", "mix")
            
            # Get matches for this segment
            seg_matches = matches.get(segment_id, [])
            if seg_matches:
                segments_with_matches += 1
            
            # Get classifier scores
            seg_scores = classifier_scores.get(segment_id, {})
            ai_prob = seg_scores.get(stem_type, 0.0)
            
            # Get consecutive match count
            n_cons = consecutive_matches.get(segment_id, 0) if consecutive_matches else 0
            
            # Get top match similarity (for fusion)
            top_sim = seg_matches[0].get("similarity", 0.0) if seg_matches else 0.0
            
            # Calculate fusion score using formula: α*p_clf + β*s_sim + γ*sigmoid(n_cons-k)
            fusion_score = self._calculate_fusion_score(
                ai_prob, top_sim, n_cons
            )
            
            # Determine final decision and confidence
            final_label = "ai" if fusion_score > 0.5 else "human"
            confidence_bucket = self._get_confidence_bucket(fusion_score)
            
            if fusion_score > 0.5:
                segments_flagged += 1
            
            # Generate evidence files if output_dir provided
            evidence_paths = {}
            if output_dir and original_file_path:
                evidence_paths = self._generate_evidence(
                    segment_id=segment_id,
                    segment=seg,
                    matches=seg_matches[:3],  # Top 3 matches
                    original_file_path=original_file_path,
                    output_dir=output_dir
                )
            
            # Build segment report
            segment_report = {
                "segment_id": segment_id,
                "file_id": seg["file_id"],
                "start": seg["start"],
                "end": seg["end"],
                "duration": seg["duration"],
                "stems": [{
                    "stem_type": stem_type,
                    "embedding_id": f"{segment_id}_{stem_type}",
                    "classifier": {
                        "ai_probability": float(ai_prob),
                        "calibrated_probability": float(ai_prob),  # Assuming already calibrated
                        "human_probability": float(1.0 - ai_prob)
                    },
                    "matches": [
                        {
                            "match_id": m.get("segment_id"),
                            "source_file_id": m.get("file_id"),
                            "similarity": m.get("similarity"),
                            "transform": m.get("transform", "none"),
                            "evidence_paths": {
                                "probe_snippet": evidence_paths.get("probe_snippet"),
                                "source_snippet": evidence_paths.get(f"source_snippet_{i}"),
                                "probe_spectrogram": evidence_paths.get("probe_spectrogram"),
                                "source_spectrogram": evidence_paths.get(f"source_spectrogram_{i}")
                            }
                        }
                        for i, m in enumerate(seg_matches[:10])  # Top 10 matches
                    ],
                    "final_decision": final_label,
                    "confidence_bucket": confidence_bucket,
                    "fusion_score": float(fusion_score),
                    "consecutive_matches": n_cons
                }],
                "match_count": len(seg_matches),
                "risk_flag": self._calculate_risk_flag_from_fusion(fusion_score, seg_matches)
            }
            
            report["segments"].append(segment_report)
            
            # Update stem statistics
            if stem_type not in stem_stats:
                stem_stats[stem_type] = {
                    "count": 0,
                    "ai_count": 0,
                    "matches_count": 0,
                    "total_ai_prob": 0.0,
                    "total_fusion_score": 0.0
                }
            stem_stats[stem_type]["count"] += 1
            if fusion_score > 0.5:
                stem_stats[stem_type]["ai_count"] += 1
            if seg_matches:
                stem_stats[stem_type]["matches_count"] += 1
            stem_stats[stem_type]["total_ai_prob"] += ai_prob
            stem_stats[stem_type]["total_fusion_score"] += fusion_score
        
        # Build stems_summary
        for stem_type, stats in stem_stats.items():
            avg_ai_prob = stats["total_ai_prob"] / stats["count"] if stats["count"] > 0 else 0.0
            avg_fusion = stats["total_fusion_score"] / stats["count"] if stats["count"] > 0 else 0.0
            report["stems_summary"].append({
                "stem_type": stem_type,
                "aggregated_ai_score": float(avg_fusion),
                "matches_found": stats["matches_count"],
                "risk_flags": "high" if avg_fusion > 0.7 else ("medium" if avg_fusion > 0.5 else "low"),
                "segment_count": stats["count"],
                "ai_segment_count": stats["ai_count"]
            })
        
        # Build overall_summary
        total_segments = len(segments)
        flag_ratio = segments_flagged / total_segments if total_segments > 0 else 0.0
        overall_ai_score = np.mean([s["fusion_score"] for seg in report["segments"] for s in seg["stems"]]) if report["segments"] else 0.0
        
        report["overall_summary"] = {
            "total_segments": total_segments,
            "segments_with_matches": segments_with_matches,
            "segments_flagged_ai": segments_flagged,
            "overall_verification_status": "verified" if flag_ratio < 0.2 else ("suspicious" if flag_ratio < 0.5 else "high_risk"),
            "overall_risk": "high" if flag_ratio > 0.5 else ("medium" if flag_ratio > 0.2 else "low"),
            "recommended_action": self._get_recommended_action(flag_ratio, overall_ai_score),
            "overall_ai_probability": float(overall_ai_score)
        }
        
        # Add metadata
        if metadata:
            report["metadata"] = metadata
        
        return report
    
    def _calculate_fusion_score(
        self,
        p_clf: float,
        s_sim: float,
        n_cons: int
    ) -> float:
        """
        Calculate fusion score using formula: α*p_clf + β*s_sim + γ*sigmoid(n_cons-k)
        
        Args:
            p_clf: Classifier probability (0-1)
            s_sim: Top match similarity (0-1)
            n_cons: Consecutive matching segments count
        """
        import math
        
        # Sigmoid function: sigmoid(n_cons - k)
        sigmoid_term = 1.0 / (1.0 + math.exp(-(n_cons - self.fusion_k)))
        
        # Fusion formula
        fusion_score = (
            self.fusion_alpha * p_clf +
            self.fusion_beta * s_sim +
            self.fusion_gamma * sigmoid_term
        )
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, fusion_score))
    
    def _get_confidence_bucket(self, fusion_score: float) -> str:
        """Get confidence bucket based on fusion score."""
        if fusion_score > 0.8 or fusion_score < 0.2:
            return "high"
        elif fusion_score > 0.6 or fusion_score < 0.4:
            return "medium"
        else:
            return "low"
    
    def _calculate_risk_flag_from_fusion(
        self,
        fusion_score: float,
        matches: List[Dict]
    ) -> str:
        """Calculate risk flag from fusion score."""
        if fusion_score > 0.8 and len(matches) > 0:
            return "high"
        elif fusion_score > 0.5 or len(matches) > 5:
            return "medium"
        else:
            return "low"
    
    def _get_recommended_action(
        self,
        flag_ratio: float,
        overall_ai_score: float
    ) -> str:
        """Get recommended action based on overall analysis."""
        if flag_ratio > 0.5 or overall_ai_score > 0.7:
            return "manual_review_required"
        elif flag_ratio > 0.2 or overall_ai_score > 0.5:
            return "review_recommended"
        else:
            return "no_action_needed"
    
    def _generate_evidence(
        self,
        segment_id: str,
        segment: Dict,
        matches: List[Dict],
        original_file_path: Path,
        output_dir: Path
    ) -> Dict[str, Optional[str]]:
        """
        Generate evidence files: audio snippets and spectrograms.
        
        Returns:
            Dictionary with paths to evidence files
        """
        evidence_dir = output_dir / "evidence" / segment_id
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        evidence_paths = {
            "probe_snippet": None,
            "probe_spectrogram": None
        }
        
        try:
            # Generate probe snippet
            probe_snippet_path = evidence_dir / "probe_snippet.wav"
            self._extract_audio_snippet(
                original_file_path,
                segment["start"],
                segment["end"],
                probe_snippet_path
            )
            evidence_paths["probe_snippet"] = str(probe_snippet_path)
            
            # Generate probe spectrogram
            probe_spec_path = evidence_dir / "probe_spectrogram.png"
            self._generate_spectrogram(probe_snippet_path, probe_spec_path)
            evidence_paths["probe_spectrogram"] = str(probe_spec_path)
            
            # Generate evidence for top matches
            for i, match in enumerate(matches[:3]):  # Top 3 matches
                source_file = match.get("file_id")
                match_start = match.get("match_start", 0.0)
                match_end = match.get("match_end", match_start + segment["duration"])
                
                # Try to find source file (this is a placeholder - actual implementation
                # would need access to source file paths)
                source_snippet_path = evidence_dir / f"source_snippet_{i}.wav"
                source_spec_path = evidence_dir / f"source_spectrogram_{i}.png"
                
                # Note: In production, you'd need to map file_id to actual file path
                # For now, we'll just create placeholder paths
                evidence_paths[f"source_snippet_{i}"] = str(source_snippet_path) if source_file else None
                evidence_paths[f"source_spectrogram_{i}"] = str(source_spec_path) if source_file else None
                
        except Exception as e:
            logger.warning(f"Failed to generate evidence for {segment_id}: {e}")
        
        return evidence_paths
    
    def _extract_audio_snippet(
        self,
        audio_path: Path,
        start_sec: float,
        end_sec: float,
        output_path: Path
    ):
        """Extract audio snippet from original file."""
        try:
            audio, sr = sf.read(audio_path)
            start_sample = int(start_sec * sr)
            end_sample = int(end_sec * sr)
            snippet = audio[start_sample:end_sample]
            sf.write(output_path, snippet, sr)
        except Exception as e:
            logger.warning(f"Failed to extract snippet: {e}")
    
    def _generate_spectrogram(self, audio_path: Path, output_path: Path):
        """Generate spectrogram image from audio file."""
        if not HAS_MATPLOTLIB:
            logger.warning("matplotlib not available, skipping spectrogram generation")
            return
        try:
            # Import librosa at function level to avoid scoping issues
            import librosa as librosa_module
            import librosa.display
            
            audio, sr = sf.read(audio_path)
            
            # Compute spectrogram using module-level librosa
            D = librosa_module.stft(audio)
            S_db = librosa_module.amplitude_to_db(np.abs(D), ref=np.max)
            
            # Remove any singleton dimensions to ensure 2D array for matplotlib
            # This fixes the error: "A should have shape (24000, 1025) not (24000, 1025, 1)"
            S_db = np.squeeze(S_db)
            
            # Ensure it's 2D (handle edge cases)
            if S_db.ndim != 2:
                if S_db.ndim == 1:
                    # Reshape 1D to 2D if needed
                    S_db = S_db.reshape(-1, 1)
                elif S_db.ndim > 2:
                    # Take first slice if 3D+
                    S_db = S_db[:, :, 0] if S_db.shape[2] == 1 else S_db.reshape(S_db.shape[0], -1)
            
            # Plot
            plt.figure(figsize=(10, 4))
            try:
                librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='hz', cmap='viridis')
            except ImportError:
                # Fallback if librosa.display not available
                plt.imshow(S_db, aspect='auto', origin='lower', cmap='viridis')
                plt.xlabel('Time')
                plt.ylabel('Frequency')
            plt.colorbar(format='%+2.0f dB')
            plt.title('Spectrogram')
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
        except Exception as e:
            logger.warning(f"Failed to generate spectrogram: {e}")
    
    def save_report(self, report: Dict, output_path: Path):
        """Save report to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Saved provenance report to {output_path}")
    
    @staticmethod
    def calculate_model_hash(model_path: Path) -> str:
        """Calculate hash of model file."""
        if not model_path.exists():
            return "unknown"
        
        sha256 = hashlib.sha256()
        with open(model_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()[:16]