"""
TTS Service - Text-to-Speech generation
"""

import asyncio
import hashlib
import subprocess
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

from core.config import get_settings
from core.logger import get_logger

logger = get_logger("tts")


@dataclass
class TTSResult:
    """TTS generation result"""
    audio_path: Path
    duration: float
    text_hash: str
    voice: str

    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        return {
            "audio_path": str(self.audio_path),
            "duration": self.duration,
            "text_hash": self.text_hash,
            "voice": self.voice,
        }


class TTSService:
    """Text-to-Speech service supporting multiple engines"""

    def __init__(self, output_dir: Optional[Path] = None):
        self.settings = get_settings()
        self.output_dir = output_dir or self.settings.OUTPUT_DIR / "tts"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._engine = self.settings.TTS_ENGINE
        self._voice = self.settings.TTS_VOICE
        self._rate = self.settings.TTS_RATE
        self._volume = self.settings.TTS_VOLUME
        
        logger.info(f"TTS Service initialized: engine={self._engine}, voice={self._voice}")

    async def generate(
        self, 
        text: str, 
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> TTSResult:
        """
        Generate speech from text
        
        Args:
            text: Text to convert to speech
            voice: Voice name (optional, uses default)
            rate: Speech rate (optional)
            output_file: Output filename (optional)
            
        Returns:
            TTSResult with audio path and metadata
        """
        voice = voice or self._voice
        rate = rate or self._rate
        
        # Generate unique filename from text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        if output_file:
            output_path = self.output_dir / output_file
        else:
            output_path = self.output_dir / f"tts_{text_hash}.wav"
        
        # Check cache
        if output_path.exists():
            duration = self._get_audio_duration(output_path)
            logger.debug(f"Using cached TTS: {output_path}")
            return TTSResult(
                audio_path=output_path,
                duration=duration,
                text_hash=text_hash,
                voice=voice
            )
        
        # Generate based on engine
        if self._engine == "edge-tts":
            await self._generate_edge_tts(text, output_path, voice, rate)
        else:
            raise ValueError(f"Unknown TTS engine: {self._engine}")
        
        duration = self._get_audio_duration(output_path)
        logger.info(f"Generated TTS: {output_path} ({duration:.1f}s)")
        
        return TTSResult(
            audio_path=output_path,
            duration=duration,
            text_hash=text_hash,
            voice=voice
        )

    async def generate_batch(
        self, 
        texts: List[str],
        voice: Optional[str] = None
    ) -> List[TTSResult]:
        """Generate multiple TTS files concurrently"""
        tasks = [self.generate(text, voice) for text in texts]
        return await asyncio.gather(*tasks)

    async def _generate_edge_tts(
        self, 
        text: str, 
        output_path: Path,
        voice: str,
        rate: str
    ):
        """Generate using edge-tts"""
        cmd = [
            "edge-tts",
            "--text", text,
            "--voice", voice,
            "--rate", rate,
            "--write-media", str(output_path)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"edge-tts failed: {error}")

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration using ffprobe"""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(audio_path)
                ],
                capture_output=True,
                text=True
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    @staticmethod
    def list_voices() -> List[str]:
        """List available voices"""
        # Common edge-tts voices
        return [
            "zh-CN-XiaoxiaoNeural",      # Chinese female
            "zh-CN-YunxiNeural",          # Chinese male  
            "zh-CN-YunyangNeural",        # Chinese male (news)
            "zh-CN-XiaoyiNeural",         # Chinese female (warm)
            "en-US-JennyNeural",          # English female
            "en-US-GuyNeural",            # English male
            "en-GB-SoniaNeural",          # British female
            "ja-JP-NanamiNeural",         # Japanese female
            "ko-KR-SunHiNeural",          # Korean female
        ]
