"""Performance tracking and reporting for the provenance pipeline."""
import time
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger = logging.getLogger(__name__)
    logger.warning("psutil not available. System metrics will not be recorded.")

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """Tracks performance metrics during pipeline execution."""
    
    def __init__(self):
        """Initialize performance tracker."""
        self.metrics = {
            "stages": {},
            "total_time": 0.0,
            "embedding_times": [],
            "search_times": [],
            "classification_times": [],
            "memory_usage": [],
            "cpu_usage": []
        }
        self.start_time = None
        if HAS_PSUTIL:
            self.process = psutil.Process(os.getpid())
        else:
            self.process = None
    
    def start(self):
        """Start tracking."""
        self.start_time = time.time()
        self.metrics["start_time"] = datetime.utcnow().isoformat()
    
    def end(self):
        """End tracking."""
        if self.start_time:
            self.metrics["total_time"] = time.time() - self.start_time
        self.metrics["end_time"] = datetime.utcnow().isoformat()
        self._record_system_metrics()
    
    def record_stage(self, stage_name: str, duration: float):
        """Record duration for a pipeline stage."""
        self.metrics["stages"][stage_name] = duration
    
    def record_embedding_time(self, duration: float):
        """Record embedding generation time."""
        self.metrics["embedding_times"].append(duration)
    
    def record_search_time(self, duration: float):
        """Record search time."""
        self.metrics["search_times"].append(duration)
    
    def record_classification_time(self, duration: float):
        """Record classification time."""
        self.metrics["classification_times"].append(duration)
    
    def _record_system_metrics(self):
        """Record current system metrics."""
        if not HAS_PSUTIL or self.process is None:
            return
        try:
            memory_info = self.process.memory_info()
            self.metrics["memory_usage"] = {
                "rss_mb": memory_info.rss / (1024 * 1024),
                "vms_mb": memory_info.vms / (1024 * 1024)
            }
            self.metrics["cpu_usage"] = {
                "percent": self.process.cpu_percent(interval=0.1),
                "num_threads": self.process.num_threads()
            }
        except Exception as e:
            logger.warning(f"Failed to record system metrics: {e}")
    
    def calculate_statistics(self) -> Dict:
        """Calculate performance statistics."""
        stats = {
            "total_time_sec": self.metrics["total_time"],
            "stages": self.metrics["stages"],
            "embedding": {},
            "search": {},
            "classification": {},
            "system": {
                "memory_mb": self.metrics.get("memory_usage", {}).get("rss_mb", 0),
                "cpu_percent": self.metrics.get("cpu_usage", {}).get("percent", 0)
            }
        }
        
        # Embedding statistics
        if self.metrics["embedding_times"]:
            embedding_times = self.metrics["embedding_times"]
            stats["embedding"] = {
                "count": len(embedding_times),
                "total_time_sec": sum(embedding_times),
                "avg_time_ms": (sum(embedding_times) / len(embedding_times)) * 1000,
                "min_time_ms": min(embedding_times) * 1000,
                "max_time_ms": max(embedding_times) * 1000,
                "throughput_emb_per_sec": len(embedding_times) / sum(embedding_times) if sum(embedding_times) > 0 else 0
            }
        
        # Search statistics
        if self.metrics["search_times"]:
            search_times = self.metrics["search_times"]
            stats["search"] = {
                "count": len(search_times),
                "avg_time_ms": (sum(search_times) / len(search_times)) * 1000,
                "min_time_ms": min(search_times) * 1000,
                "max_time_ms": max(search_times) * 1000
            }
        
        # Classification statistics
        if self.metrics["classification_times"]:
            class_times = self.metrics["classification_times"]
            stats["classification"] = {
                "count": len(class_times),
                "avg_time_ms": (sum(class_times) / len(class_times)) * 1000
            }
        
        return stats
    
    def generate_report(
        self,
        output_path: Path,
        target_latency: float = 1.0,
        target_throughput: float = 10.0,
        target_embedding_ms: float = 50.0
    ) -> Dict:
        """
        Generate performance report.
        
        Args:
            output_path: Path to save report JSON
            target_latency: Target latency in seconds (default: 1.0)
            target_throughput: Target throughput (embeddings/sec) (default: 10.0)
            target_embedding_ms: Target embedding time in ms (default: 50.0)
        """
        stats = self.calculate_statistics()
        
        # Add targets and compliance
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "performance": stats,
            "targets": {
                "latency_sec": target_latency,
                "throughput_emb_per_sec": target_throughput,
                "embedding_time_ms": target_embedding_ms
            },
            "compliance": {
                "meets_latency": stats["total_time_sec"] <= target_latency,
                "meets_throughput": stats["embedding"].get("throughput_emb_per_sec", 0) >= target_throughput,
                "meets_embedding_time": stats["embedding"].get("avg_time_ms", float('inf')) <= target_embedding_ms
            },
            "environment": {
                "cpu_count": psutil.cpu_count() if HAS_PSUTIL else 0,
                "memory_total_gb": psutil.virtual_memory().total / (1024**3) if HAS_PSUTIL else 0
            }
        }
        
        # Save report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Performance report saved to {output_path}")
        return report

