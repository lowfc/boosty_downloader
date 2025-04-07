from unittest.mock import patch, mock_open
from datetime import datetime
from pathlib import Path
import json
from core.sync_data import SyncData


class TestSyncData:
    def test_initialization(self):
        """Тестирование инициализации объекта"""
        test_path = Path("/test/path")
        sync_data = SyncData(test_path)

        assert sync_data._SyncData__path == test_path
        assert sync_data.creator_name == ""
        assert sync_data.last_sync_utc is None
        assert sync_data.last_photo_offset is None
        assert sync_data.last_audio_offset is None
        assert sync_data.last_video_offset is None
        assert sync_data.last_posts_offset is None

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dumps")
    def test_save(self, mock_json_dumps, mock_file_open):
        """Тестирование сохранения данных"""
        test_path = Path("/test/path")
        sync_data = SyncData(test_path)
        sync_data.creator_name = "test_creator"
        test_time = datetime.now()
        sync_data.last_sync_utc = test_time
        sync_data.last_photo_offset = "photo123"
        sync_data.last_audio_offset = "audio456"
        sync_data.last_video_offset = "video789"
        sync_data.last_posts_offset = "posts000"

        # Настраиваем мок для json.dumps
        mock_json_dumps.return_value = "test_json_data"

        sync_data.save()

        # Проверяем вызовы
        mock_file_open.assert_called_once_with(test_path, "w")
        mock_json_dumps.assert_called_once_with({
            "creator_name": "test_creator",
            "last_sync_utc": test_time.isoformat(),
            "last_photo_offset": "photo123",
            "last_audio_offset": "audio456",
            "last_video_offset": "video789",
            "last_posts_offset": "posts000",
        }, indent=2)
        mock_file_open().write.assert_called_once_with("test_json_data")

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
        "creator_name": "loaded_creator",
        "last_sync_utc": "2023-01-01T00:00:00",
        "last_photo_offset": "loaded_photo",
        "last_audio_offset": "loaded_audio",
        "last_video_offset": "loaded_video",
        "last_posts_offset": "loaded_posts",
    }))
    def test_load_success(self, mock_file_open):
        """Тестирование успешной загрузки данных"""
        test_path = Path("/test/path")
        expected_time = datetime(2023, 1, 1)

        result = SyncData.load(test_path)

        assert result is not None
        assert result._SyncData__path == test_path
        assert result.creator_name == "loaded_creator"
        assert result.last_sync_utc == expected_time
        assert result.last_photo_offset == "loaded_photo"
        assert result.last_audio_offset == "loaded_audio"
        assert result.last_video_offset == "loaded_video"
        assert result.last_posts_offset == "loaded_posts"

        mock_file_open.assert_called_once_with(test_path, "r")

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("core.logger.logger.warning")
    def test_load_file_not_found(self, mock_logger, mock_file_open):
        """Тестирование случая, когда файл не найден"""
        test_path = Path("/nonexistent/path")

        result = SyncData.load(test_path)

        assert result is None
        mock_file_open.assert_called_once_with(test_path, "r")
        mock_logger.assert_called_once_with(f"meta file is not exists at {test_path}")

    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    @patch("core.logger.logger.error")
    def test_load_invalid_json(self, mock_logger, mock_file_open):
        """Тестирование случая с невалидным JSON"""
        test_path = Path("/invalid/json/path")

        result = SyncData.load(test_path)

        assert result is None
        mock_file_open.assert_called_once_with(test_path, "r")
        assert mock_logger.call_count == 1
        assert "Failed parse meta file" in mock_logger.call_args[0][0]

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
        "invalid_key": "value"
    }))
    @patch("core.logger.logger.error")
    def test_load_invalid_format(self, mock_logger, mock_file_open):
        """Тестирование случая с неверным форматом данных"""
        test_path = Path("/invalid/format/path")

        result = SyncData.load(test_path)

        assert result is None
        mock_file_open.assert_called_once_with(test_path, "r")
        mock_logger.assert_called_once_with("Unknown meta file format, failed parse")

    @patch("builtins.open", side_effect=Exception("Test error"))
    @patch("core.logger.logger.error")
    def test_load_general_exception(self, mock_logger, mock_file_open):
        """Тестирование обработки общего исключения без сравнения объектов исключений"""
        test_path = Path("/error/path")

        result = SyncData.load(test_path)

        assert result is None
        mock_file_open.assert_called_once_with(test_path, "r")

        # Проверяем что logger.error был вызван ровно один раз
        assert mock_logger.call_count == 1

        # Проверяем текст сообщения об ошибке
        args, kwargs = mock_logger.call_args
        assert args[0] == "Failed parse meta file"

        # Проверяем что был передан exc_info и это Exception
        assert "exc_info" in kwargs
        assert isinstance(kwargs["exc_info"], Exception)
        assert str(kwargs["exc_info"]) == "Test error"
