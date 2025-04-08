import pytest
from unittest.mock import patch
from core.stat_tracker import StatTracker, stat_tracker


class TestStatTracker:

    def setup_method(self):
        """Сбрасываем состояние трекера перед каждым тестом"""
        stat_tracker._StatTracker__downloaded_photo = 0
        stat_tracker._StatTracker__passed_photo = 0
        stat_tracker._StatTracker__error_photo = 0
        stat_tracker._StatTracker__downloaded_video = 0
        stat_tracker._StatTracker__passed_video = 0
        stat_tracker._StatTracker__error_video = 0
        stat_tracker._StatTracker__downloaded_audio = 0
        stat_tracker._StatTracker__passed_audio = 0
        stat_tracker._StatTracker__error_audio = 0
        stat_tracker._StatTracker__downloaded_file = 0
        stat_tracker._StatTracker__passed_file = 0
        stat_tracker._StatTracker__error_file = 0
        stat_tracker.total_photos = 0
        stat_tracker.total_videos = 0
        stat_tracker.total_audios = 0
        stat_tracker._StatTracker__download_errors = []

    def test_add_downloaded_photo(self):
        stat_tracker.add_downloaded_photo()
        assert stat_tracker._StatTracker__downloaded_photo == 1

    def test_add_passed_photo(self):
        stat_tracker.add_passed_photo()
        assert stat_tracker._StatTracker__passed_photo == 1

    def test_add_error_photo(self):
        stat_tracker.add_error_photo()
        assert stat_tracker._StatTracker__error_photo == 1

    def test_add_downloaded_video(self):
        stat_tracker.add_downloaded_video()
        assert stat_tracker._StatTracker__downloaded_video == 1

    def test_add_passed_video(self):
        stat_tracker.add_passed_video()
        assert stat_tracker._StatTracker__passed_video == 1

    def test_add_error_video(self):
        stat_tracker.add_error_video()
        assert stat_tracker._StatTracker__error_video == 1

    def test_add_downloaded_audio(self):
        stat_tracker.add_downloaded_audio()
        assert stat_tracker._StatTracker__downloaded_audio == 1

    def test_add_passed_audio(self):
        stat_tracker.add_passed_audio()
        assert stat_tracker._StatTracker__passed_audio == 1

    def test_add_error_audio(self):
        stat_tracker.add_error_audio()
        assert stat_tracker._StatTracker__error_audio == 1

    def test_add_downloaded_file(self):
        stat_tracker.add_downloaded_file()
        assert stat_tracker._StatTracker__downloaded_file == 1

    def test_add_passed_file(self):
        stat_tracker.add_passed_file()
        assert stat_tracker._StatTracker__passed_file == 1

    def test_add_error_file(self):
        stat_tracker.add_error_file()
        assert stat_tracker._StatTracker__error_file == 1

    def test_add_download_error(self):
        test_url = "http://example.com/file.jpg"
        stat_tracker.add_download_error(test_url)
        assert test_url in stat_tracker._StatTracker__download_errors
        assert len(stat_tracker._StatTracker__download_errors) == 1

    def test_str_representation_no_errors(self):
        stat_tracker.total_photos = 10
        stat_tracker.total_videos = 5
        stat_tracker.total_audios = 3

        stat_tracker.add_downloaded_photo()
        stat_tracker.add_passed_photo()
        stat_tracker.add_error_photo()

        result = str(stat_tracker)
        assert "Photo Stat" in result
        assert "Video Stat" in result
        assert "Audio Stat" in result
        assert "File Stat" in result
        assert "WARNING: Downloading of some files failed!" not in result

    def test_str_representation_with_errors(self):
        stat_tracker.total_photos = 10
        stat_tracker.add_download_error("http://example.com/error.jpg")

        result = str(stat_tracker)
        assert "WARNING: Downloading of some files failed!" in result
        assert "http://example.com/error.jpg" in result

    @patch('builtins.print')
    def test_show_summary(self, mock_print):
        stat_tracker.show_summary()
        assert mock_print.called
        assert mock_print.call_args[0][0].startswith('\n\n')

