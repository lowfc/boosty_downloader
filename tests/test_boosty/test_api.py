import pytest
from unittest.mock import AsyncMock, patch
from aiohttp import ClientSession
from boosty.api import (
    get_media_list,
)


class TestApi:
    @pytest.mark.asyncio
    async def test_get_media_list_success(self):
        """Тестирование успешного получения списка медиа"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": {}, "extra": {}}
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response

        result = await get_media_list(
            session=mock_session,
            media_type="image",
            creator_name="test_creator",
            use_cookie=True
        )

        assert result == {"data": {}, "extra": {}}

    @pytest.mark.asyncio
    @patch('core.logger.logger.error')
    async def test_get_media_list_error(self, mock_logger):
        """Тестирование ошибки при получении списка медиа"""
        mock_session = AsyncMock(ClientSession)
        mock_session.get.side_effect = Exception("Test error")

        result = await get_media_list(
            session=mock_session,
            media_type="image",
            creator_name="test_creator",
            use_cookie=True
        )

        assert result is None
        assert mock_logger.call_count == 1
        args, kwargs = mock_logger.call_args
        assert args[0] == "Failed get media album"
