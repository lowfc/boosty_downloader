import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path


from core.utils import (
    create_dir_if_not_exists,
    create_text_document,
    parse_creator_name,
    parse_bool,
    print_summary,
    parse_offset_time,
)


@patch("os.path.isdir")
@patch("os.mkdir")
@patch("core.logger.logger.info")
def test_create_dir_if_not_exists_exists(mock_logger, mock_mkdir, mock_isdir):
    mock_isdir.return_value = True
    path = Path("/existing/dir")
    create_dir_if_not_exists(path)
    mock_mkdir.assert_not_called()
    mock_logger.assert_not_called()


@patch("os.path.isdir")
@patch("os.mkdir")
@patch("core.logger.logger.info")
def test_create_dir_if_not_exists_not_exists(mock_logger, mock_mkdir, mock_isdir):
    mock_isdir.return_value = False
    path = Path("/new/dir")
    create_dir_if_not_exists(path)
    mock_mkdir.assert_called_once_with(path)
    mock_logger.assert_called_once_with(f"create directory: {path}")


# Тесты для create_text_document
@pytest.mark.asyncio
async def test_create_text_document():
    path = Path("/test/dir")
    content = "test content"
    ext = "txt"
    name = "test_file"

    # Создаем асинхронный мок для aiofiles.open
    mock_file = MagicMock()
    mock_file.__aenter__.return_value.write = AsyncMock(return_value=None)
    mock_file.__aexit__.return_value = None

    with patch("aiofiles.open", return_value=mock_file) as mock_aiofiles_open:
        await create_text_document(path, content, ext, name)

    # Проверяем вызовы
    expected_path = path / f"{name}.{ext}"
    mock_aiofiles_open.assert_called_once_with(expected_path, "w", encoding="utf-8")
    mock_file.__aenter__.return_value.write.assert_awaited_once_with(content)


# Тесты для parse_creator_name
@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("boosty.to/creator", "creator"),
        ("boosty.to/creator/", "creator"),
        ("https://boosty.to/creator", "creator"),
        ("invalid_input", "invalid_input"),
        ("", ""),
    ],
)
def test_parse_creator_name(input_str: str, expected: str):
    assert parse_creator_name(input_str) == expected


# Тесты для parse_bool
@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("y", True),
        ("yes", True),
        ("1", True),
        ("t", True),
        ("true", True),
        ("n", False),
        ("no", False),
        ("0", False),
        ("false", False),
        ("", False),
        ("invalid", False),
    ],
)
def test_parse_bool(input_str: str, expected: bool):
    assert parse_bool(input_str) == expected


# Тесты для print_summary
@patch("core.utils.print_colorized")
def test_print_summary(mock_print_colorized):
    creator_name = "test_creator"
    use_cookie = True
    sync_dir = "/test/dir"
    download_timeout = 120
    need_load_video = True
    need_load_photo = False
    need_load_audio = True
    need_load_files = False
    storage_type = "local"

    print_summary(
        creator_name,
        use_cookie,
        sync_dir,
        download_timeout,
        need_load_video,
        need_load_photo,
        need_load_audio,
        need_load_files,
        storage_type,
    )

    assert mock_print_colorized.call_count == 9


# Тесты для parse_offset_time
@patch("core.logger.logger.error")
def test_parse_offset_time_valid(mock_logger_error):
    assert parse_offset_time("10:30") == 10
    mock_logger_error.assert_not_called()


@patch("core.logger.logger.error")
def test_parse_offset_time_invalid(mock_logger_error):
    assert parse_offset_time("invalid") is None
    mock_logger_error.assert_called_once_with("Failed parse offset invalid")


@patch("core.logger.logger.error")
def test_parse_offset_time_empty(mock_logger_error):
    assert parse_offset_time("") is None
    mock_logger_error.assert_not_called()
