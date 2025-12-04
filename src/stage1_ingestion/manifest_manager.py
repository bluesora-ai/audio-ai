"""Manifest generation for dataset management and reproducibility."""
import csv
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)


class ManifestManager:
    """Manages manifest files for files, anchors, and augmented benchmarks."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize manifest manager.
        
        Args:
            output_dir: Directory where manifests will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_files_manifest(
        self,
        files: List[Dict],
        manifest_path: Optional[Path] = None
    ) -> Path:
        """
        Generate files_manifest.csv.
        
        Expected columns:
        file_id,filename,path,duration_sec,sample_rate,bit_depth,label(human|AI),stem_types,genre,uploaded_at,source
        """
        if manifest_path is None:
            manifest_path = self.output_dir / "files_manifest.csv"
        
        with open(manifest_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'file_id', 'filename', 'path', 'duration_sec', 'sample_rate',
                'bit_depth', 'label', 'stem_types', 'genre', 'uploaded_at', 'source'
            ])
            writer.writeheader()
            
            for file_info in files:
                writer.writerow({
                    'file_id': file_info.get('file_id', ''),
                    'filename': file_info.get('filename', ''),
                    'path': file_info.get('path', ''),
                    'duration_sec': file_info.get('duration_sec', 0.0),
                    'sample_rate': file_info.get('sample_rate', 44100),
                    'bit_depth': file_info.get('bit_depth', 16),
                    'label': file_info.get('label', 'unknown'),
                    'stem_types': ','.join(file_info.get('stem_types', [])),
                    'genre': file_info.get('genre', ''),
                    'uploaded_at': file_info.get('uploaded_at', datetime.utcnow().isoformat()),
                    'source': file_info.get('source', '')
                })
        
        logger.info(f"Generated files manifest: {manifest_path}")
        return manifest_path
    
    def generate_anchors_manifest(
        self,
        anchors: List[Dict],
        manifest_path: Optional[Path] = None
    ) -> Path:
        """
        Generate anchors_manifest.csv.
        
        Expected columns:
        anchor_id,file_id,stem_type,start_sec,end_sec,path,sample_rate,duration_sec
        """
        if manifest_path is None:
            manifest_path = self.output_dir / "anchors_manifest.csv"
        
        with open(manifest_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'anchor_id', 'file_id', 'stem_type', 'start_sec', 'end_sec',
                'path', 'sample_rate', 'duration_sec'
            ])
            writer.writeheader()
            
            for anchor in anchors:
                writer.writerow({
                    'anchor_id': anchor.get('anchor_id', ''),
                    'file_id': anchor.get('file_id', ''),
                    'stem_type': anchor.get('stem_type', 'mix'),
                    'start_sec': anchor.get('start_sec', 0.0),
                    'end_sec': anchor.get('end_sec', 0.0),
                    'path': anchor.get('path', ''),
                    'sample_rate': anchor.get('sample_rate', 44100),
                    'duration_sec': anchor.get('duration_sec', 0.0)
                })
        
        logger.info(f"Generated anchors manifest: {manifest_path}")
        return manifest_path
    
    def generate_augmented_benchmark_manifest(
        self,
        augmented_samples: List[Dict],
        manifest_path: Optional[Path] = None
    ) -> Path:
        """
        Generate augmented_benchmark_manifest.csv.
        
        Expected columns:
        aug_id,anchor_id,augmentation_name,params,path
        """
        if manifest_path is None:
            manifest_path = self.output_dir / "augmented_benchmark_manifest.csv"
        
        with open(manifest_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'aug_id', 'anchor_id', 'augmentation_name', 'params', 'path'
            ])
            writer.writeheader()
            
            for aug in augmented_samples:
                params_str = json.dumps(aug.get('params', {})) if isinstance(aug.get('params'), dict) else str(aug.get('params', ''))
                writer.writerow({
                    'aug_id': aug.get('aug_id', ''),
                    'anchor_id': aug.get('anchor_id', ''),
                    'augmentation_name': aug.get('augmentation_name', ''),
                    'params': params_str,
                    'path': aug.get('path', '')
                })
        
        logger.info(f"Generated augmented benchmark manifest: {manifest_path}")
        return manifest_path
    
    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

