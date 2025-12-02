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
        logger.info(f"  Total segments: {report['summary']['total_segments']}")
        logger.info(f"  Segments with matches: {report['summary']['segments_with_matches']}")
        logger.info(f"  Segments flagged as AI: {report['summary']['segments_flagged_ai']}")
        logger.info(f"  Overall risk level: {report['summary']['risk_level']}")
        
        # Show sample segment results
        if report['segments']:
            logger.info(f"\nSample segment results (first 3):")
            for seg in report['segments'][:3]:
                logger.info(f"  {seg['segment_id']}:")
                logger.info(f"    Stem: {seg['stem_type']}")
                logger.info(f"    AI Probability: {seg['classifier']['ai_probability']:.3f}")
                logger.info(f"    Matches: {seg['match_count']}")
                logger.info(f"    Risk: {seg['risk_flag']}")
        
    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

