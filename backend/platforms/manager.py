"""
Multi-platform streaming manager
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import asyncio
from dataclasses import asdict

from platforms.base import PlatformAdapter, PlatformConfig, PlatformStatus
from platforms.adapters import create_adapter, ADAPTER_REGISTRY
from core.config import get_settings, PLATFORM_CONFIGS
from core.exceptions import PlatformNotConfiguredError, PlatformError
from core.logger import get_logger

logger = get_logger("platforms")


class PlatformManager:
    """Manages multiple streaming platforms"""

    def __init__(self, config_file: Optional[Path] = None):
        self._adapters: Dict[str, PlatformAdapter] = {}
        self._config_file = config_file
        self.settings = get_settings()

        # Initialize platforms from settings
        self._init_from_settings()

        # Load saved configurations
        if config_file and config_file.exists():
            self._load_configurations()

    def _init_from_settings(self):
        """Initialize platforms from environment settings"""
        for platform_type, config in PLATFORM_CONFIGS.items():
            stream_key = getattr(self.settings, config["stream_key_env"], None)
            rtmp_url = getattr(self.settings, config["rtmp_url_env"], None) or config["default_rtmp"]

            if stream_key:
                self.add_platform(
                    platform_type=platform_type,
                    rtmp_url=rtmp_url,
                    stream_key=stream_key,
                    enabled=True
                )
                logger.info(f"Initialized platform: {platform_type}")

    def _load_configurations(self):
        """Load saved platform configurations"""
        try:
            with open(self._config_file, 'r') as f:
                configs = json.load(f)
            for platform_type, config in configs.items():
                if platform_type not in self._adapters:
                    self.add_platform(
                        platform_type=platform_type,
                        rtmp_url=config.get("rtmp_url", ""),
                        stream_key=config.get("stream_key", ""),
                        enabled=config.get("enabled", False)
                    )
        except Exception as e:
            logger.warning(f"Failed to load platform configurations: {e}")

    def _save_configurations(self):
        """Save platform configurations"""
        if not self._config_file:
            return

        configs = {}
        for platform_type, adapter in self._adapters.items():
            configs[platform_type] = {
                "rtmp_url": adapter.config.rtmp_url,
                "stream_key": adapter.config.stream_key,
                "enabled": adapter.config.enabled,
            }

        try:
            with open(self._config_file, 'w') as f:
                json.dump(configs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save platform configurations: {e}")

    def add_platform(
        self,
        platform_type: str,
        rtmp_url: str,
        stream_key: str,
        enabled: bool = True
    ) -> Optional[PlatformAdapter]:
        """Add or update a platform"""
        if platform_type not in ADAPTER_REGISTRY:
            logger.error(f"Unknown platform type: {platform_type}")
            return None

        config = PlatformConfig(
            name=PLATFORM_CONFIGS.get(platform_type, {}).get("name", platform_type),
            platform_type=platform_type,
            rtmp_url=rtmp_url,
            stream_key=stream_key,
            enabled=enabled,
            video_params=PLATFORM_CONFIGS.get(platform_type, {}).get("video_params", {})
        )

        adapter = create_adapter(platform_type, config)
        if adapter:
            self._adapters[platform_type] = adapter
            self._save_configurations()
            logger.info(f"Added platform: {platform_type}")

        return adapter

    def remove_platform(self, platform_type: str) -> bool:
        """Remove a platform"""
        if platform_type in self._adapters:
            del self._adapters[platform_type]
            self._save_configurations()
            logger.info(f"Removed platform: {platform_type}")
            return True
        return False

    def get_platform(self, platform_type: str) -> Optional[PlatformAdapter]:
        """Get a platform adapter"""
        return self._adapters.get(platform_type)

    def get_all_platforms(self) -> Dict[str, PlatformAdapter]:
        """Get all platform adapters"""
        return self._adapters.copy()

    def get_enabled_platforms(self) -> List[PlatformAdapter]:
        """Get all enabled platforms"""
        return [a for a in self._adapters.values() if a.is_enabled]

    def get_configured_platforms(self) -> List[PlatformAdapter]:
        """Get all properly configured platforms"""
        return [a for a in self._adapters.values() if a.config.is_configured()]

    def enable_platform(self, platform_type: str) -> bool:
        """Enable a platform"""
        adapter = self._adapters.get(platform_type)
        if adapter:
            adapter.config.enabled = True
            self._save_configurations()
            return True
        return False

    def disable_platform(self, platform_type: str) -> bool:
        """Disable a platform"""
        adapter = self._adapters.get(platform_type)
        if adapter:
            adapter.config.enabled = False
            self._save_configurations()
            return True
        return False

    def update_stream_key(self, platform_type: str, stream_key: str) -> bool:
        """Update stream key for a platform"""
        adapter = self._adapters.get(platform_type)
        if adapter:
            adapter.config.stream_key = stream_key
            self._save_configurations()
            return True
        return False

    def get_ffmpeg_tee_command(self, platform_types: Optional[List[str]] = None) -> str:
        """
        Generate FFmpeg tee command for multi-platform streaming

        Args:
            platform_types: Specific platforms to stream to, or None for all enabled

        Returns:
            FFmpeg tee output string
        """
        if platform_types:
            platforms = [self._adapters.get(p) for p in platform_types if p in self._adapters]
        else:
            platforms = self.get_enabled_platforms()

        if not platforms:
            raise PlatformNotConfiguredError("No enabled platforms configured")

        # Build tee outputs
        tee_outputs = []
        for adapter in platforms:
            if adapter.config.is_configured():
                tee_outputs.append(f"[f=flv]{adapter.config.full_rtmp_url}")

        if not tee_outputs:
            raise PlatformNotConfiguredError("No properly configured platforms")

        return f'"tee:' + "|".join(tee_outputs) + '"'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "platforms": {
                p_type: adapter.to_dict()
                for p_type, adapter in self._adapters.items()
            },
            "available_platforms": list(ADAPTER_REGISTRY.keys()),
            "enabled_count": len(self.get_enabled_platforms()),
            "configured_count": len(self.get_configured_platforms()),
        }


# Global instance
_platform_manager: Optional[PlatformManager] = None


def get_platform_manager() -> PlatformManager:
    """Get the global platform manager instance"""
    global _platform_manager
    if _platform_manager is None:
        config_file = get_settings().OUTPUT_DIR / "platform_config.json"
        _platform_manager = PlatformManager(config_file)
    return _platform_manager
