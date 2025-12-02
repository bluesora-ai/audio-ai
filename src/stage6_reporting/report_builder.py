"""Provenance report builder for Milestone 2."""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)


class ProvenanceReportBuilder:
    """Builds provenance reports with matches, classifier scores, and metadata."""
    
    def __init__(
        self,
        model_hash: Optional[str] = None,
        index_hash: Optional[str] = None
    ):
        """
        Initialize report builder.
        
        Args:
            model_hash: Hash of embedding model
            index_hash: Hash of FAISS index
        """
        self.model_hash = model_hash
        self.index_hash = index_hash
        self.timestamp = datetime.utcnow().isoformat()
    
    def build_report(
        self,
        file_id: str,
        segments: List[Dict],
        matches: Dict[str, List[Dict]],  # segment_id -> list of matches
        classifier_scores: Dict[str, Dict],  # segment_id -> {stem_type: prob}
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Build complete provenance report.
        
        Args:
            file_id: Original file identifier
            segments: List of segment metadata
            matches: Dictionary of matches per segment
            classifier_scores: Dictionary of classifier scores per segment/stem
            metadata: Additional metadata
        
        Returns:
            Complete provenance report dictionary
        """
        report = {
            "file_id": file_id,
            "timestamp": self.timestamp,
            "model_provenance": {
                "model_hash": self.model_hash,
                "index_hash": self.index_hash,
                "embedding_dim": 512,
                "model_type": "openl3"  # or "mert" if using MERT
            },
            "segments": [],
            "summary": {
                "total_segments": len(segments),
                "segments_with_matches": 0,
                "segments_flagged_ai": 0,
                "risk_level": "low"
            }
        }
        
        segments_flagged = 0
        segments_with_matches = 0
        
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
            
            if ai_prob > 0.5:
                segments_flagged += 1
            
            # Build segment report
            segment_report = {
                "segment_id": segment_id,
                "file_id": seg["file_id"],
                "start": seg["start"],
                "end": seg["end"],
                "duration": seg["duration"],
                "stem_type": stem_type,
                "classifier": {
                    "ai_probability": float(ai_prob),
                    "human_probability": float(1.0 - ai_prob),
                    "prediction": "ai" if ai_prob > 0.5 else "human",
                    "confidence": float(abs(ai_prob - 0.5) * 2)  # 0-1 scale
                },
                "matches": [
                    {
                        "match_id": m.get("segment_id"),
                        "source_file": m.get("file_id"),
                        "similarity": m.get("similarity"),
                        "distance": m.get("distance"),
                        "rank": m.get("rank"),
                        "match_start": m.get("start"),
                        "match_end": m.get("end")
                    }
                    for m in seg_matches[:10]  # Top 10 matches
                ],
                "match_count": len(seg_matches),
                "risk_flag": self._calculate_risk_flag(ai_prob, seg_matches)
            }
            
            report["segments"].append(segment_report)
        
        # Update summary
        report["summary"]["segments_with_matches"] = segments_with_matches
        report["summary"]["segments_flagged_ai"] = segments_flagged
        report["summary"]["risk_level"] = self._calculate_overall_risk(
            segments_flagged, len(segments), matches
        )
        
        # Add metadata
        if metadata:
            report["metadata"] = metadata
        
        return report
    
    def _calculate_risk_flag(
        self,
        ai_prob: float,
        matches: List[Dict]
    ) -> str:
        """Calculate risk flag for a segment."""
        if ai_prob > 0.8 and len(matches) > 0:
            return "high"
        elif ai_prob > 0.5 or len(matches) > 5:
            return "medium"
        else:
            return "low"
    
    def _calculate_overall_risk(
        self,
        segments_flagged: int,
        total_segments: int,
        all_matches: Dict
    ) -> str:
        """Calculate overall risk level."""
        flag_ratio = segments_flagged / total_segments if total_segments > 0 else 0
        
        if flag_ratio > 0.5:
            return "high"
        elif flag_ratio > 0.2:
            return "medium"
        else:
            return "low"
    
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