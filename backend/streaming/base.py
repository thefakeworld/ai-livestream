"""
Base streaming class
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import subprocess
import threading
import time
from pathlib import Path

from core.logger import get_logger
from core.exceptions import StreamingError, StreamConnectionError, FFmpegError

logger = get_logger("streaming")


class StreamStatus(Enum):
    """Stream status enum"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class StreamInfo:
    """Stream information"""
    status: StreamStatus = StreamStatus.IDLE
    start_time: Optional[float] = None
    duration: float = 0
    frames_sent: int = 0
    bitrate: str = "0"
    error_message: Optional[str] = None
    current_content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "start_time": self.start_time,
            "duration": self.duration,
            "frames_sent": self.frames_sent,
            "bitrate": self.bitrate,
            "error_message": self.error_message,
            "current_content": self.current_content,
        }


class BaseStreamer(ABC):
    """Base class for all streamers"""

    def __init__(self):
        self._status = StreamInfo()
        self._process: Optional[subprocess.Popen] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def status(self) -> StreamInfo:
        return self._status

    @property
    def is_running(self) -> bool:
        return self._status.status == StreamStatus.RUNNING

    @abstractmethod
    def build_command(self) -> List[str]:
        """Build the FFmpeg command"""
        pass

    def start(self) -> bool:
        """Start streaming"""
        if self.is_running:
            logger.warning("Streamer is already running")
            return False

        try:
            self._status.status = StreamStatus.STARTING
            self._stop_event.clear()

            cmd = self.build_command()
            logger.info(f"Starting stream with command: {' '.join(cmd[:10])}...")

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
            )

            self._status.status = StreamStatus.RUNNING
            self._status.start_time = time.time()
            self._status.error_message = None

            # Start monitor thread
            self._monitor_thread = threading.Thread(
                target=self._monitor_process,
                daemon=True
            )
            self._monitor_thread.start()

            logger.info("Stream started successfully")
            return True

        except Exception as e:
            self._status.status = StreamStatus.ERROR
            self._status.error_message = str(e)
            logger.error(f"Failed to start stream: {e}")
            return False

    def stop(self) -> bool:
        """Stop streaming"""
        if not self.is_running:
            return False

        try:
            self._status.status = StreamStatus.STOPPING
            self._stop_event.set()

            if self._process:
                # Send quit command to FFmpeg
                try:
                    self._process.communicate(input=b'q', timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.terminate()
                    self._process.wait(timeout=5)
                except Exception:
                    self._process.kill()

            self._process = None
            self._status.status = StreamStatus.IDLE
            logger.info("Stream stopped")
            return True

        except Exception as e:
            self._status.status = StreamStatus.ERROR
            self._status.error_message = str(e)
            logger.error(f"Error stopping stream: {e}")
            return False

    def _monitor_process(self):
        """Monitor FFmpeg process"""
        while not self._stop_event.is_set() and self._process:
            if self._process.poll() is not None:
                # Process has ended
                return_code = self._process.returncode
                if return_code != 0:
                    stderr = self._process.stderr.read().decode('utf-8', errors='ignore')
                    self._status.status = StreamStatus.ERROR
                    self._status.error_message = f"FFmpeg exited with code {return_code}: {stderr[-500:]}"
                    logger.error(f"FFmpeg process ended: {return_code}")
                break

            # Update duration
            if self._status.start_time:
                self._status.duration = time.time() - self._status.start_time

            time.sleep(1)

    def restart(self) -> bool:
        """Restart streaming"""
        self.stop()
        time.sleep(2)
        return self.start()
