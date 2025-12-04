"""Inspect and validate provenance report structure."""
import json
import sys
from pathlib import Path
from typing import Dict, List

def print_section(title):
    print(f"\n{'='*70}")
    print(f"{title}")
    print('='*70)

def inspect_report(report_path: Path):
    """Inspect a provenance report file."""
    if not report_path.exists():
        print(f"❌ Report file not found: {report_path}")
        return False
    
    print_section("PROVENANCE REPORT INSPECTION")
    print(f"File: {report_path}")
    
    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
    except Exception as e:
        print(f"❌ Error reading report: {e}")
        return False
    
    # 1. Basic Info
    print_section("1. Basic Information")
    print(f"File ID: {report.get('file_id', 'N/A')}")
    print(f"Timestamp: {report.get('timestamp', 'N/A')}")
    print(f"Processing Time: {report.get('processing_time_sec', 'N/A')}s")
    
    # 2. Summary
    print_section("2. Summary")
    summary = report.get('summary', {})
    print(f"Total Segments: {summary.get('total_segments', 0)}")
    print(f"Total Stems: {summary.get('total_stems', 0)}")
    print(f"Risk Level: {summary.get('risk_level', 'N/A')}")
    print(f"AI Probability: {summary.get('ai_probability', 0):.3f}")
    print(f"Human Probability: {summary.get('human_probability', 0):.3f}")
    print(f"Flagged Segments: {summary.get('flagged_segments', 0)}")
    
    # 3. Segments
    print_section("3. Segment Analysis")
    segments = report.get('segments', [])
    print(f"Total Segments: {len(segments)}")
    
    if segments:
        # Show first 3 segments
        for i, seg in enumerate(segments[:3], 1):
            print(f"\n  Segment {i}:")
            print(f"    ID: {seg.get('segment_id', 'N/A')}")
            print(f"    Time: {seg.get('start', 0):.2f}s - {seg.get('end', 0):.2f}s")
            print(f"    Stem: {seg.get('stem_type', 'N/A')}")
            print(f"    AI Probability: {seg.get('ai_probability', 0):.3f}")
            
            matches = seg.get('matches', [])
            if matches:
                print(f"    Top Match Similarity: {matches[0].get('similarity', 0):.3f}")
                print(f"    Top Match Source: {matches[0].get('source_id', 'N/A')}")
            else:
                print(f"    No matches found")
        
        if len(segments) > 3:
            print(f"\n  ... and {len(segments) - 3} more segments")
    
    # 4. Model Provenance
    print_section("4. Model Provenance")
    model_prov = report.get('model_provenance', {})
    print(f"Embedding Model: {model_prov.get('model_name', 'N/A')}")
    print(f"Model Version: {model_prov.get('model_version', 'N/A')}")
    print(f"Model Checksum: {model_prov.get('model_checksum', 'N/A')[:16]}..." if model_prov.get('model_checksum') else "N/A")
    print(f"Embedding Dimension: {model_prov.get('embedding_dim', 'N/A')}")
    
    # 5. Index Provenance
    print_section("5. Index Provenance")
    index_prov = report.get('index_provenance', {})
    print(f"Index Type: {index_prov.get('index_type', 'N/A')}")
    print(f"Total Vectors: {index_prov.get('total_vectors', 0)}")
    print(f"Index Checksum: {index_prov.get('index_checksum', 'N/A')[:16]}..." if index_prov.get('index_checksum') else "N/A")
    print(f"Index Version: {index_prov.get('index_version', 'N/A')}")
    
    # 6. Evidence Paths
    print_section("6. Evidence Files")
    evidence = report.get('evidence', {})
    if evidence:
        print(f"Spectrograms: {len(evidence.get('spectrograms', []))} files")
        print(f"Audio Snippets: {len(evidence.get('audio_snippets', []))} files")
        print(f"Match Snippets: {len(evidence.get('match_snippets', []))} files")
    else:
        print("No evidence files listed")
    
    # 7. Validation
    print_section("7. Structure Validation")
    required_fields = [
        'file_id', 'timestamp', 'summary', 'segments',
        'model_provenance', 'index_provenance'
    ]
    
    missing = [f for f in required_fields if f not in report]
    if missing:
        print(f"❌ Missing required fields: {missing}")
        return False
    else:
        print("✅ All required fields present")
    
    # Check summary fields
    summary_required = ['total_segments', 'risk_level', 'ai_probability']
    summary_missing = [f for f in summary_required if f not in summary]
    if summary_missing:
        print(f"⚠️  Missing summary fields: {summary_missing}")
    else:
        print("✅ Summary fields complete")
    
    # Check segment structure
    if segments:
        first_seg = segments[0]
        seg_required = ['segment_id', 'start', 'end', 'ai_probability']
        seg_missing = [f for f in seg_required if f not in first_seg]
        if seg_missing:
            print(f"⚠️  Missing segment fields: {seg_missing}")
        else:
            print("✅ Segment structure valid")
    
    print_section("INSPECTION COMPLETE")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python inspect_report.py <report.json>")
        print("\nExample:")
        print("  python inspect_report.py test_reports/report_abc123.json")
        return 1
    
    report_path = Path(sys.argv[1])
    success = inspect_report(report_path)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

