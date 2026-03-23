"""
Director module - Intelligent content management
"""

from typing import Optional, Dict, Any
import threading
import time
from dataclasses import dataclass
from enum import Enum

from core.config import get_settings
from core.logger import get_logger
from streaming import FFmpegStreamer

logger = get_logger("director")


class DirectorState(Enum):
    """Director states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class DirectorStatus:
    """Director status information"""
    state: DirectorState = DirectorState.IDLE
    current_content: Optional[str] = None
    uptime: float = 0
    content_switched: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "state": self.state.value,
            "current_content": self.current_content,
            "uptime": self.uptime,
            "content_switched": self.content_switched,
        }


class Director:
    """Intelligent director for content management"""

    def __init__(self):
        self.settings = get_settings()
        self._status = DirectorStatus()
        self._streamer: Optional[FFmpegStreamer] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def status(self) -> DirectorStatus:
        return self._status

    @property
    def is_running(self) -> bool:
        return self._status.state == DirectorState.RUNNING

    def start(self):
        """Start the director"""
        if self.is_running:
            return False

        self._stop_event.clear()
        self._status.state = DirectorState.RUNNING

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        logger.info("Director started")
        return True

    def stop(self):
        """Stop the director"""
        self._stop_event.set()
        self._status.state = DirectorState.IDLE

        if self._streamer and self._streamer.is_running:
            self._streamer.stop()

        logger.info("Director stopped")
        return True

    def _run_loop(self):
        """Main director loop"""
        while not self._stop_event.is_set():
            try:
                # Director logic here
                # - Check content queue
                # - Switch content when needed
                # - Update status
                time.sleep(1)

            except Exception as e:
                logger.error(f"Director error: {e}")
                self._status.state = DirectorState.ERROR

    def switch_content(self, content_type: str, content_id: str = None):
        """Switch to different content"""
        logger.info(f"Switching to {content_type}: {content_id}")
        # TODO: Implement content switching logic
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "state": self._status.state.value,
            "current_content": self._status.current_content,
            "uptime": self._status.uptime,
            "content_switched": self._status.content_switched,
        }
