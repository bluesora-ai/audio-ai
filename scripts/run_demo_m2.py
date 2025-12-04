"""Milestone 2 demonstration script - Complete provenance pipeline."""
import sys
from pathlib import Path
import logging
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import PipelineOrchestrator
from config.settings import (
    FAISS_INDEX_PATH, FAISS_METADATA_PATH, CLASSIFIER_PATHS,
    MODELS_DIR, REPORTS_DIR
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Run Milestone 2 complete pipeline demo."""
    logger.info("=" * 60)
    logger.info("Milestone 2: Complete Provenance Pipeline")
    logger.info("=" * 60)
    
    # Setup paths
    data_dir = Path("data")
    input_audio = data_dir / "raw" / "test_audio.wav"
    
    if not input_audio.exists():
        logger.error(f"Input audio file not found: {input_audio}")
        logger.info("Please place a test audio file at: data/raw/test_audio.wav")
        return
    
    # Initialize orchestrator
    logger.info("\nInitializing pipeline orchestrator...")
    
    # Check if models/index exist
    index_path = FAISS_INDEX_PATH if FAISS_INDEX_PATH.exists() else None
    metadata_path = FAISS_METADATA_PATH if FAISS_METADATA_PATH.exists() else None
    
    classifier_paths = {}
    for stem_type, path in CLASSIFIER_PATHS.items():
        if path.exists():
            classifier_paths[stem_type] = path
    
    if not classifier_paths:
        logger.warning("No classifier models found. Classification will use default probabilities.")
    
    orchestrator = PipelineOrchestrator(
        index_path=index_path,
        metadata_path=metadata_path,
        classifier_paths=classifier_paths if classifier_paths else None
    )
    
    # Process file
    logger.info(f"\nProcessing file: {input_audio}")
    output_dir = data_dir / "processing" / input_audio.stem
    
    try:
        report = orchestrator.process_file(
            input_path=input_audio,
            output_dir=output_dir
        )
        
        # Save report
        report_path = REPORTS_DIR / f"demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("\n" + "=" * 60)
        logger.info("Milestone 2 Demo Complete!")
        logger.info("=" * 60)
        logger.info(f"✓ Report saved to: {report_path}")
        logger.info(f"\nReport Summary:")
        
        # Use overall_summary instead of summary (new structure)
        overall = report.get('overall_summary', {})
        logger.info(f"  Total segments: {overall.get('total_segments', 0)}")
        logger.info(f"  Segments with matches: {overall.get('segments_with_matches', 0)}")
        logger.info(f"  Segments flagged as AI: {overall.get('segments_flagged_ai', 0)}")
        logger.info(f"  Overall risk level: {overall.get('overall_risk', 'unknown')}")
        logger.info(f"  Verification status: {overall.get('overall_verification_status', 'unknown')}")
        logger.info(f"  Recommended action: {overall.get('recommended_action', 'unknown')}")
        logger.info(f"  Overall AI probability: {overall.get('overall_ai_probability', 0.0):.3f}")
        
        # Show sample segment results
        if report.get('segments'):
            logger.info(f"\nSample segment results (first 3):")
            for seg in report['segments'][:3]:
                logger.info(f"  {seg.get('segment_id', 'unknown')}:")
                
                # New structure has stems[] array
                if 'stems' in seg and len(seg['stems']) > 0:
                    stem_info = seg['stems'][0]
                    logger.info(f"    Stem: {stem_info.get('stem_type', 'unknown')}")
                    classifier = stem_info.get('classifier', {})
                    logger.info(f"    AI Probability: {classifier.get('ai_probability', 0.0):.3f}")
                    logger.info(f"    Fusion Score: {stem_info.get('fusion_score', 0.0):.3f}")
                    logger.info(f"    Consecutive Matches: {stem_info.get('consecutive_matches', 0)}")
                    logger.info(f"    Final Decision: {stem_info.get('final_decision', 'unknown')}")
                    logger.info(f"    Matches: {seg.get('match_count', 0)}")
                    logger.info(f"    Risk: {seg.get('risk_flag', 'unknown')}")
                else:
                    # Fallback for old structure
                    logger.info(f"    Stem: {seg.get('stem_type', 'unknown')}")
                    logger.info(f"    Matches: {seg.get('match_count', 0)}")
                    logger.info(f"    Risk: {seg.get('risk_flag', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

