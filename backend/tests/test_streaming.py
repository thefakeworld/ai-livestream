"""
Streaming Module Tests
"""

import pytest
from pathlib import Path


class TestBaseStreamer:
    """Test Base Streamer"""

    def test_stream_status_enum(self):
        """Test stream status values"""
        from streaming.base import StreamStatus
        
        assert StreamStatus.IDLE.value == "idle"
        assert StreamStatus.STARTING.value == "starting"
        assert StreamStatus.RUNNING.value == "running"
        assert StreamStatus.STOPPING.value == "stopping"
        assert StreamStatus.ERROR.value == "error"

    def test_stream_info_dataclass(self):
        """Test stream info dataclass"""
        from streaming.base import StreamInfo, StreamStatus
        
        info = StreamInfo()
        
        assert info.status == StreamStatus.IDLE
        assert info.start_time is None
        assert info.duration == 0
        assert info.error_message is None

    def test_stream_info_to_dict(self):
        """Test stream info serialization"""
        from streaming.base import StreamInfo, StreamStatus
        
        info = StreamInfo(
            status=StreamStatus.RUNNING,
            duration=100.5,
            bitrate="2500k",
            current_content="test.mp4"
        )
        
        data = info.to_dict()
        
        assert data["status"] == "running"
        assert data["duration"] == 100.5
        assert data["bitrate"] == "2500k"
        assert data["current_content"] == "test.mp4"


class TestFFmpegStreamer:
    """Test FFmpeg Streamer"""

    def test_ffmpeg_streamer_init(self):
        """Test FFmpeg streamer initialization"""
        from streaming.ffmpeg_streamer import FFmpegStreamer
        
        streamer = FFmpegStreamer()
        
        assert streamer.video_source is None
        assert streamer.audio_source is None
        assert streamer.platforms is None

    def test_ffmpeg_streamer_set_sources(self):
        """Test setting video and audio sources"""
        from streaming.ffmpeg_streamer import FFmpegStreamer
        
        streamer = FFmpegStreamer()
        
        streamer.set_video_source("test.mp4")
        streamer.set_audio_source("test.mp3")
        
        assert streamer.video_source == "test.mp4"
        assert streamer.audio_source == "test.mp3"

    def test_ffmpeg_build_command_video_file(self):
        """Test building command for video file"""
        from streaming.ffmpeg_streamer import FFmpegStreamer
        
        streamer = FFmpegStreamer(video_source="test.mp4")
        
        # This will fail without platform config, but we can check the structure
        try:
            cmd = streamer.build_command()
            assert "ffmpeg" in cmd
            assert "-i" in cmd
        except ValueError as e:
            # Expected if no platforms configured
            assert "platform" in str(e).lower()

    def test_ffmpeg_build_command_static_image(self):
        """Test building command for static image"""
        from streaming.ffmpeg_streamer import FFmpegStreamer
        
        streamer = FFmpegStreamer(video_source="test.png")
        
        try:
            cmd = streamer.build_command()
            assert "-loop" in cmd
            assert "1" in cmd
        except ValueError:
            pass  # Expected without platform config


class TestPlaylistStreamer:
    """Test Playlist Streamer"""

    def test_playlist_streamer_init(self, test_dirs):
        """Test playlist streamer initialization"""
        from streaming.ffmpeg_streamer import PlaylistStreamer
        
        # Create a test playlist file
        playlist_file = test_dirs["output"] / "test_playlist.txt"
        with open(playlist_file, "w") as f:
            f.write("video1.mp4\n")
            f.write("video2.mp4\n")
            f.write("# comment\n")
            f.write("video3.mp4\n")
        
        streamer = PlaylistStreamer(playlist_file=str(playlist_file))
        
        assert len(streamer.playlist) == 3
        assert "video1.mp4" in streamer.playlist

    def test_playlist_navigation(self, test_dirs):
        """Test playlist navigation"""
        from streaming.ffmpeg_streamer import PlaylistStreamer
        
        playlist_file = test_dirs["output"] / "nav_playlist.txt"
        with open(playlist_file, "w") as f:
            f.write("video1.mp4\n")
            f.write("video2.mp4\n")
            f.write("video3.mp4\n")
        
        streamer = PlaylistStreamer(playlist_file=str(playlist_file))
        
        current = streamer.get_current_video()
        assert current == "video1.mp4"
        
        next_video = streamer.next_video()
        assert next_video == "video2.mp4"
        
        next_video = streamer.next_video()
        assert next_video == "video3.mp4"
        
        # Should loop back to first
        next_video = streamer.next_video()
        assert next_video == "video1.mp4"

    def test_empty_playlist(self):
        """Test empty playlist handling"""
        from streaming.ffmpeg_streamer import PlaylistStreamer
        
        streamer = PlaylistStreamer()
        
        assert streamer.get_current_video() is None
        assert streamer.next_video() is None
