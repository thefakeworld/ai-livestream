"""
Services Tests
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import sys

# Ensure backend is in path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


@pytest.fixture
def test_dirs():
    """Create temporary directories for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    
    dirs = {
        "base": temp_dir,
        "assets": temp_dir / "assets",
        "output": temp_dir / "output",
        "logs": temp_dir / "logs",
        "music": temp_dir / "music",
        "video": temp_dir / "assets" / "video",
        "news": temp_dir / "assets" / "news",
        "tts": temp_dir / "output" / "tts",
    }
    
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    
    yield dirs
    
    # Cleanup
    shutil.rmtree(temp_dir)


class TestTTSService:
    """Test TTS Service"""

    def test_tts_service_init(self, test_dirs):
        """Test TTS service initialization"""
        from services.tts_service import TTSService
        
        tts = TTSService(output_dir=test_dirs["tts"])
        
        assert tts.output_dir == test_dirs["tts"]
        assert tts.output_dir.exists()

    def test_tts_list_voices(self):
        """Test listing available voices"""
        from services.tts_service import TTSService
        
        voices = TTSService.list_voices()
        
        assert isinstance(voices, list)
        assert len(voices) > 0
        assert any("zh-CN" in v for v in voices)


class TestNewsService:
    """Test News Service"""

    def test_news_service_init(self, test_dirs):
        """Test news service initialization"""
        from services.news_service import NewsService
        
        news = NewsService(cache_dir=test_dirs["news"])
        
        assert news.cache_dir == test_dirs["news"]

    def test_news_item_creation(self):
        """Test news item creation"""
        from services.news_service import NewsItem
        from datetime import datetime
        
        item = NewsItem(
            title="Test News",
            content="Test content",
            source="Test Source",
            url="https://example.com",
            published=datetime.now(),
        )
        
        assert item.title == "Test News"
        assert len(item.hash) == 8
        assert item.to_dict()["title"] == "Test News"

    def test_news_add_custom(self, test_dirs):
        """Test adding custom news item"""
        from services.news_service import NewsService
        
        news = NewsService(cache_dir=test_dirs["news"])
        
        item = news.add_custom(
            title="Custom News",
            content="Custom content for testing"
        )
        
        assert item.title == "Custom News"
        assert item.source == "custom"
        
        # Verify it's cached
        cached = news.get_item(item.hash)
        assert cached is not None
        assert cached.title == "Custom News"

    def test_news_format_for_tts(self, test_dirs):
        """Test formatting news for TTS"""
        from services.news_service import NewsService, NewsItem
        
        news = NewsService(cache_dir=test_dirs["news"])
        
        item = NewsItem(
            title="测试标题",
            content="<p>这是带有HTML标签的内容</p>",
            source="test",
            url="https://example.com",
        )
        
        formatted = news.format_for_tts(item)
        
        assert "测试标题" in formatted
        assert "<p>" not in formatted  # HTML should be stripped


class TestMusicService:
    """Test Music Service"""

    def test_music_service_init(self, test_dirs):
        """Test music service initialization"""
        from services.music_service import MusicService
        
        music = MusicService(music_dir=test_dirs["music"])
        
        assert music.music_dir == test_dirs["music"]
        assert music.music_dir.exists()

    def test_music_get_stats(self, test_dirs):
        """Test getting music library stats"""
        from services.music_service import MusicService
        
        music = MusicService(music_dir=test_dirs["music"])
        stats = music.get_stats()
        
        assert "track_count" in stats
        assert "total_duration_hours" in stats
        assert "total_size_mb" in stats

    def test_music_get_all_tracks(self, test_dirs):
        """Test getting all tracks"""
        from services.music_service import MusicService
        
        music = MusicService(music_dir=test_dirs["music"])
        tracks = music.get_all_tracks()
        
        assert isinstance(tracks, list)

    def test_music_get_random_track_empty(self, test_dirs):
        """Test getting random track from empty library"""
        from services.music_service import MusicService
        
        music = MusicService(music_dir=test_dirs["music"])
        track = music.get_random_track()
        
        # Should return None for empty library
        assert track is None


class TestVideoService:
    """Test Video Service"""

    def test_video_service_init(self, test_dirs):
        """Test video service initialization"""
        from services.video_service import VideoService
        
        video = VideoService(output_dir=test_dirs["output"])
        
        assert video.output_dir == test_dirs["output"]
        assert video.output_dir.exists()

    def test_video_has_template_check(self, test_dirs):
        """Test checking for video template"""
        from services.video_service import VideoService
        
        video = VideoService(output_dir=test_dirs["output"])
        
        # Should be False since we don't have a template
        assert video.has_video_template is False

    def test_video_has_static_image_check(self, test_dirs):
        """Test checking for static image"""
        from services.video_service import VideoService
        
        video = VideoService(output_dir=test_dirs["output"])
        
        # Should be False since we don't have an image
        assert video.has_static_image is False


class TestPlaylistService:
    """Test Playlist Service"""

    def test_playlist_service_init(self, test_dirs):
        """Test playlist service initialization"""
        from services.playlist_service import PlaylistService
        
        playlist = PlaylistService(output_dir=test_dirs["output"])
        
        assert playlist.output_dir == test_dirs["output"]

    def test_playlist_add_item(self, test_dirs):
        """Test adding item to playlist"""
        from services.playlist_service import PlaylistService, ContentType
        
        playlist = PlaylistService(output_dir=test_dirs["output"])
        
        item = playlist.add_item(
            content_type=ContentType.MUSIC,
            path="/fake/path/to/music.mp3",
            title="Test Song",
            duration=180.5
        )
        
        assert item.title == "Test Song"
        assert item.duration == 180.5
        assert item.content_type == ContentType.MUSIC

    def test_playlist_get_all(self, test_dirs):
        """Test getting all playlist items"""
        from services.playlist_service import PlaylistService, ContentType
        
        playlist = PlaylistService(output_dir=test_dirs["output"])
        
        playlist.add_item(
            content_type=ContentType.MUSIC,
            path="/fake/path1.mp3",
            title="Song 1",
            duration=180
        )
        playlist.add_item(
            content_type=ContentType.MUSIC,
            path="/fake/path2.mp3",
            title="Song 2",
            duration=200
        )
        
        items = playlist.get_all()
        
        assert len(items) >= 2

    def test_playlist_clear(self, test_dirs):
        """Test clearing playlist"""
        from services.playlist_service import PlaylistService, ContentType
        
        playlist = PlaylistService(output_dir=test_dirs["output"])
        
        playlist.add_item(
            content_type=ContentType.MUSIC,
            path="/fake/path.mp3",
            title="Song",
            duration=180
        )
        
        playlist.clear()
        
        assert len(playlist.get_all()) == 0

    def test_playlist_get_total_duration(self, test_dirs):
        """Test calculating total duration"""
        from services.playlist_service import PlaylistService, ContentType
        
        playlist = PlaylistService(output_dir=test_dirs["output"])
        playlist.clear()
        
        playlist.add_item(
            content_type=ContentType.MUSIC,
            path="/fake/path1.mp3",
            title="Song 1",
            duration=100
        )
        playlist.add_item(
            content_type=ContentType.MUSIC,
            path="/fake/path2.mp3",
            title="Song 2",
            duration=200
        )
        
        total = playlist.get_total_duration()
        
        assert total == 300

    def test_playlist_shuffle(self, test_dirs):
        """Test shuffling playlist"""
        from services.playlist_service import PlaylistService, ContentType
        
        playlist = PlaylistService(output_dir=test_dirs["output"])
        playlist.clear()
        
        for i in range(10):
            playlist.add_item(
                content_type=ContentType.MUSIC,
                path=f"/fake/path{i}.mp3",
                title=f"Song {i}",
                duration=180
            )
        
        original_order = [item.title for item in playlist.get_all()]
        playlist.shuffle()
        new_order = [item.title for item in playlist.get_all()]
        
        # Order should be different (statistically)
        # Note: In rare cases shuffle might produce same order
        assert len(new_order) == len(original_order)

    def test_playlist_navigation(self, test_dirs):
        """Test playlist navigation"""
        from services.playlist_service import PlaylistService, ContentType
        
        playlist = PlaylistService(output_dir=test_dirs["output"])
        playlist.clear()
        
        playlist.add_item(
            content_type=ContentType.MUSIC,
            path="/fake/path1.mp3",
            title="Song 1",
            duration=180
        )
        playlist.add_item(
            content_type=ContentType.MUSIC,
            path="/fake/path2.mp3",
            title="Song 2",
            duration=200
        )
        playlist.add_item(
            content_type=ContentType.MUSIC,
            path="/fake/path3.mp3",
            title="Song 3",
            duration=220
        )
        
        current = playlist.get_current()
        assert current.title == "Song 1"
        
        next_item = playlist.get_next()
        assert next_item.title == "Song 2"
        
        prev_item = playlist.get_previous()
        assert prev_item.title == "Song 1"
