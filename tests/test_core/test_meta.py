import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

from core.meta import parse_metadata, write_video_metadata


# Тесты для parse_metadata
@pytest.mark.parametrize(
    "post, media, expected",
    [
        (
            {"title": "Test Title"},
            {"preview": "http://example.com/cover.jpg"},
            {"title": "Test Title", "cover": "http://example.com/cover.jpg"},
        ),
        ({"title": "Test Title"}, {}, {"title": "Test Title"}),
        ({}, {"preview": "http://example.com/cover.jpg"}, {"cover": "http://example.com/cover.jpg"}),
        ({}, {}, {}),
    ],
)
def test_parse_metadata(post, media, expected):
    assert parse_metadata(post, media) == expected


# Общий мок для MP4
class MockMP4:
    def __init__(self, *args, **kwargs):
        self.tags = {}

    def __setitem__(self, key, value):
        self.tags[key] = value

    def save(self):
        pass


# Тесты для write_video_metadata
@pytest.mark.asyncio
async def test_write_video_metadata_no_metadata():
    with patch('core.meta.MP4', new=MockMP4):
        await write_video_metadata(Path("/test.mp4"), None)
        # Ничего не должно вызываться


@pytest.mark.asyncio
async def test_write_video_metadata_with_title():
    with patch('core.meta.MP4', new=MockMP4), \
            patch.object(MockMP4, 'save') as mock_save:
        await write_video_metadata(Path("/test.mp4"), {"title": "Test Title"})

        mock_save.assert_called_once()
        # Дополнительные проверки tags можно добавить при необходимости


@pytest.mark.asyncio
async def test_write_video_metadata_with_cover():
    mock_session = AsyncMock()
    mock_resp = AsyncMock()
    mock_resp.read = AsyncMock(return_value=b"image_data")
    mock_session.__aenter__.return_value.get.return_value = mock_resp

    with patch('core.meta.MP4', new=MockMP4), \
            patch('aiohttp.ClientSession', return_value=mock_session), \
            patch.object(MockMP4, 'save') as mock_save:
        await write_video_metadata(
            Path("/test.mp4"),
            {"title": "Test", "cover": "http://test.com/cover.jpg"}
        )

        mock_session.__aenter__.return_value.get.assert_called_once_with(
            "http://test.com/cover.jpg"
        )
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_write_video_metadata_exception():
    class FailingMP4:
        def __init__(self, *args, **kwargs):
            raise Exception("Test error")

    with patch('core.meta.MP4', new=FailingMP4), \
            patch('core.logger.logger.exception') as mock_logger:
        await write_video_metadata(Path("/test.mp4"), {"title": "Test"})

        # Проверяем что logger.exception был вызван ровно один раз
        assert mock_logger.call_count == 1

        # Проверяем текст сообщения
        args, kwargs = mock_logger.call_args
        assert args[0] == "Error writing metadata"

        # Проверяем что был передан exc_info и Exception
        assert 'exc_info' in kwargs
        assert isinstance(kwargs['exc_info'], Exception)
        assert str(kwargs['exc_info']) == "Test error"
