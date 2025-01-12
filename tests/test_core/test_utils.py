import pytest
from pathlib import Path
from unittest.mock import patch

from core.utils import create_dir_if_not_exists, download_file_if_not_exists


def test_create_dir_if_not_exists_path_not_exists():
    file = Path("./dummy-dir")
    with patch('os.mkdir') as mock_mkdir:
        create_dir_if_not_exists(file)

        mock_mkdir.assert_called_once()
        assert mock_mkdir.call_args[0][0] == file


def test_create_dir_if_not_exists_path_exists():
    file = Path("./dummy-dir")
    with patch('os.path.isdir') as mock_isdir:
        mock_isdir.return_value = True

        with patch('os.mkdir') as mock_mkdir:
            create_dir_if_not_exists(file)
            mock_mkdir.assert_not_called()

        mock_isdir.assert_called_once()
        assert mock_isdir.call_args[0][0] == file


@pytest.mark.asyncio
async def test_download_file_if_not_exists_file_not_exists():
    file = Path("./dummy-file.txt")
    url = "https://google.com/"
    with patch('os.path.isfile') as mock_isfile:
        mock_isfile.return_value = False
        with patch('core.utils.download_file') as mock_download:
            mock_download.return_value = True
            res = await download_file_if_not_exists(url=url, path=file)
            mock_download.assert_called_once()
            assert res
            assert mock_download.call_args[0][0] == url
            assert mock_download.call_args[0][1] == file
        mock_isfile.assert_called_once()


@pytest.mark.asyncio
async def test_download_file_if_not_exists_file_exists():
    file = Path("./dummy-file.txt")
    url = "https://google.com/"
    with patch('os.path.isfile') as mock_isfile:
        mock_isfile.return_value = True
        with patch('core.utils.download_file') as mock_download:
            res = await download_file_if_not_exists(url=url, path=file)
            mock_download.assert_not_called()
            assert not res
        mock_isfile.assert_called_once()
