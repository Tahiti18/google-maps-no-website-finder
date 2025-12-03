"""Background worker for processing scans."""
import logging
import threading
import queue
from uuid import UUID
from typing import Optional

from app.services.scanner import ScannerService

logger = logging.getLogger(__name__)


class ScanWorker:
    """Simple background worker for processing scan jobs."""
    
    _instance: Optional['ScanWorker'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure one worker instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize worker."""
        if not hasattr(self, 'initialized'):
            self.job_queue: queue.Queue = queue.Queue()
            self.scanner_service = ScannerService()
            self.worker_thread: Optional[threading.Thread] = None
            self.running = False
            self.initialized = True
    
    def start(self):
        """Start the worker thread."""
        if self.running:
            logger.warning("Worker already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Worker thread started")
    
    def stop(self):
        """Stop the worker thread."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Worker thread stopped")
    
    def submit_scan(self, scan_id: UUID):
        """
        Submit a scan job to the queue.
        
        Args:
            scan_id: Scan ID to process
        """
        self.job_queue.put(scan_id)
        logger.info(f"Scan {scan_id} submitted to queue")
    
    def _worker_loop(self):
        """Main worker loop that processes jobs from the queue."""
        logger.info("Worker loop started")
        
        while self.running:
            try:
                # Wait for a job with timeout to allow checking running flag
                scan_id = self.job_queue.get(timeout=1)
                
                try:
                    logger.info(f"Processing scan {scan_id}")
                    self.scanner_service.process_scan(scan_id)
                except Exception as e:
                    logger.error(f"Error processing scan {scan_id}: {e}", exc_info=True)
                finally:
                    self.job_queue.task_done()
            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
        
        logger.info("Worker loop ended")


# Global worker instance
_worker: Optional[ScanWorker] = None


def get_worker() -> ScanWorker:
    """
    Get the global worker instance.
    
    Returns:
        ScanWorker instance
    """
    global _worker
    if _worker is None:
        _worker = ScanWorker()
    return _worker
