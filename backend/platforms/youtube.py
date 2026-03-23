"""
YouTube platform adapter
"""

from platforms.base import PlatformAdapter, PlatformConfig


class YouTubeAdapter(PlatformAdapter):
    """YouTube Live streaming adapter"""

    @property
    def platform_type(self) -> str:
        return "youtube"

    @property
    def display_name(self) -> str:
        return "YouTube"

    def get_ffmpeg_video_params(self) -> list:
        params = super().get_ffmpeg_video_params()
        # YouTube specific optimizations
        params.extend([
            "-profile:v", "high",
            "-level", "4.2",
        ])
        return params


def create_youtube_adapter(rtmp_url: str, stream_key: str, enabled: bool = True) -> YouTubeAdapter:
    """Factory function to create YouTube adapter"""
    config = PlatformConfig(
        name="YouTube",
        platform_type="youtube",
        rtmp_url=rtmp_url,
        stream_key=stream_key,
        enabled=enabled,
        video_params={
            "preset": "veryfast",
            "g": 60,
            "profile": "high",
        }
    )
    return YouTubeAdapter(config)
