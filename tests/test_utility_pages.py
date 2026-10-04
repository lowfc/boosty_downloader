import asyncio
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from core.downloads_manager import DownloadManager
from pages.download_image_by_link import DownloadImageByLinkPage
from pages.merge_author_content import MergeAuthorContentPage

IMAGE_ID = "9b981067-9854-4af0-aed4-6b5efe3ad96f"
IMAGE_LINK = f"https://boosty.to/test-author/blog/media/053713d9-93df-4f4a-ae45-e01ea031cb15/{IMAGE_ID}"


class AsyncContext:
    def __init__(self, value):
        self.value = value
        self.exited = False

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *args):
        self.exited = True


class ImagePageTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.page = DownloadImageByLinkPage(DownloadManager())
        self.page.update = Mock()
        self.page.set_destination(self.folder)
        self.page.text_field.value = IMAGE_LINK
        self.settings = patch(
            "pages.download_image_by_link.get_download_settings",
            new=AsyncMock(
                return_value=SimpleNamespace(chunk_size=1500, download_timeout=100)
            ),
        )
        self.settings.start()
        self.addCleanup(self.settings.stop)
        self.logger = patch("pages.download_image_by_link.logger")
        self.logger.start()
        self.addCleanup(self.logger.stop)

    def client_for(self, stream, length=6):
        response = SimpleNamespace(
            content_length=length,
            raise_for_status=Mock(),
            content=SimpleNamespace(iter_chunked=Mock(return_value=stream)),
        )
        response_context = AsyncContext(response)
        session = SimpleNamespace(get=Mock(return_value=response_context))
        session_context = AsyncContext(session)
        client = Mock()
        client.get_client_session.return_value = session_context
        return client, session, response_context, session_context

    async def test_invalid_links_and_missing_folders_never_start_network(self):
        with patch("pages.download_image_by_link.BoostyClient") as client:
            for link in ("", "bad", "https://boosty.to/author/posts/id"):
                self.page.text_field.value = link
                await self.page.download_image()
                self.assertIn("Check the image link", self.page.status_text.value)
            self.page.text_field.value = IMAGE_LINK
            self.page.set_destination(self.folder / "missing")
            await self.page.download_image()
            self.assertIn("existing download folder", self.page.status_text.value)
        client.assert_not_called()
        self.assertFalse(self.page.busy)

    async def test_success_preserves_existing_images_and_restores_controls(self):
        async def chunks():
            yield b"abc"
            yield b"def"

        client, session, response_context, session_context = self.client_for(chunks())
        with patch("pages.download_image_by_link.BoostyClient", return_value=client):
            await self.page.download_image()
            self.assertEqual((self.folder / f"{IMAGE_ID}.jpg").read_bytes(), b"abcdef")
            self.assertEqual(self.page.status_text.value, "Image saved.")
            await self.page.download_image()
            self.assertIn("already saved", self.page.status_text.value)
        session.get.assert_called_once_with(
            f"https://images.boosty.to/image/{IMAGE_ID}"
        )
        self.assertTrue(response_context.exited and session_context.exited)
        self.assertFalse(self.page.busy)
        self.assertFalse(self.page.download_button.disabled)
        self.assertFalse(self.page.destination_folder_picker.disabled)
        self.assertFalse(self.page.progress.visible)
        self.assertEqual((self.folder / f"{IMAGE_ID}.jpg").read_bytes(), b"abcdef")

    async def test_failed_or_cancelled_download_removes_partial_file(self):
        async def broken_chunks():
            yield b"partial"
            raise OSError("network disconnected")

        client, *_ = self.client_for(broken_chunks())
        with patch("pages.download_image_by_link.BoostyClient", return_value=client):
            await self.page.download_image()
        self.assertFalse((self.folder / f"{IMAGE_ID}.jpg").exists())
        self.assertIn("Couldn't download", self.page.status_text.value)
        self.assertFalse(self.page.busy)

        entered = asyncio.Event()

        async def waiting_chunks():
            yield b"partial"
            entered.set()
            await asyncio.Event().wait()

        client, _, response_context, session_context = self.client_for(waiting_chunks())
        with patch("pages.download_image_by_link.BoostyClient", return_value=client):
            task = asyncio.create_task(self.page.download_image())
            await asyncio.wait_for(entered.wait(), timeout=3)
            self.page.will_unmount()
            updates = self.page.update.call_count
            await asyncio.gather(task, return_exceptions=True)
        self.assertTrue(task.cancelled())
        self.assertTrue(response_context.exited and session_context.exited)
        self.assertFalse((self.folder / f"{IMAGE_ID}.jpg").exists())
        self.assertEqual(self.page.update.call_count, updates)

    async def test_saved_folder_clipboard_and_picker_use_real_values(self):
        with patch(
            "pages.download_image_by_link.get_destination_folder",
            new=AsyncMock(return_value=str(self.folder)),
        ):
            await self.page.load_destination()
        self.assertEqual(self.page.destination_path, self.folder)
        self.assertEqual(self.page.destination.tooltip, str(self.folder))
        with patch("pages.post_download_form.ft.Clipboard") as clipboard:
            clipboard.return_value.get = AsyncMock(return_value=" " + IMAGE_LINK + " ")
            await self.page.paste_link()
        self.assertEqual(self.page.text_field.value, IMAGE_LINK)
        with patch("pages.download_image_by_link.ft.FilePicker") as picker:
            picker.return_value.get_directory_path = AsyncMock(return_value=None)
            await self.page.pick_destination_folder()
            self.assertEqual(self.page.destination_path, self.folder)
            other = self.folder / "other"
            other.mkdir()
            picker.return_value.get_directory_path.return_value = str(other)
            await self.page.pick_destination_folder()
        self.assertEqual(self.page.destination_path, other)
        self.assertEqual(self.page.folder_note.tooltip, str(other))


class MergePageTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.root = self.folder / "downloads"
        self.author = self.root / "test-author"
        self.first = self.author / "first-post"
        self.second = self.author / "second-post"
        self.first.mkdir(parents=True)
        self.second.mkdir()
        (self.first / "photo.jpg").write_bytes(b"first photo")
        (self.second / "photo.jpg").write_bytes(b"second photo")
        (self.first / "video.mp4").write_bytes(b"video")
        (self.first / "audio.mp3").write_bytes(b"audio")
        (self.first / "post.txt").write_bytes(b"text")
        self.destination = self.folder / "collection"
        self.destination.mkdir()
        self.page = MergeAuthorContentPage(DownloadManager())
        self.page.update = Mock()
        self.page.settings = SimpleNamespace(downloads_folder=str(self.root))
        with patch(
            "pages.merge_author_content.get_download_settings",
            new=AsyncMock(return_value=self.page.settings),
        ):
            await self.page.load_main_options()
        self.page.authors_dropdown.value = "test-author"
        self.page.destination_path = self.destination
        self.page.update_state()
        logger = patch("pages.merge_author_content.logger")
        logger.start()
        self.addCleanup(logger.stop)

    async def test_copy_filters_content_and_skips_collisions_without_overwriting(self):
        await self.page.do_merge()
        self.assertEqual((self.destination / "photo.jpg").read_bytes(), b"first photo")
        self.assertEqual((self.destination / "video.mp4").read_bytes(), b"video")
        self.assertFalse((self.destination / "audio.mp3").exists())
        self.assertFalse((self.destination / "post.txt").exists())
        self.assertTrue((self.first / "photo.jpg").exists())
        self.assertTrue((self.second / "photo.jpg").exists())
        self.assertIn("Skipped 1 existing files", self.page.description_text.value)
        self.assertEqual(self.page.status_text.value, "Content copied.")
        self.assertFalse(self.page.form.disabled)
        self.assertFalse(self.page.busy)
        self.assertFalse(self.page.progress_ring.visible)

    async def test_move_and_post_title_only_transfer_selected_files(self):
        self.page.select_action("move")
        self.page.merge_photos_check.value = False
        self.page.merge_videos_check.value = False
        self.page.merge_audios_check.value = True
        self.page.add_post_title_to_filename.value = True
        self.page.update_state()
        self.assertEqual(self.page.proceed_button.content, "Move content")
        await self.page.do_merge()
        self.assertEqual(
            (self.destination / "first-post_audio.mp3").read_bytes(), b"audio"
        )
        self.assertFalse((self.first / "audio.mp3").exists())
        self.assertTrue((self.first / "photo.jpg").exists())
        self.assertTrue((self.first / "video.mp4").exists())
        self.assertEqual(self.page.status_text.value, "Content moved.")

    async def test_failed_transfer_reports_partial_result_and_keeps_form_usable(self):
        original_copy = shutil.copy

        def copy(source, target):
            if source.suffix == ".mp4":
                raise PermissionError("read-only destination")
            return original_copy(source, target)

        with patch("pages.merge_author_content.shutil.copy", side_effect=copy):
            await self.page.do_merge()
        self.assertTrue((self.destination / "photo.jpg").exists())
        self.assertFalse((self.destination / "video.mp4").exists())
        self.assertIn("Some files", self.page.status_text.value)
        self.assertIn(
            "1 files could not be transferred", self.page.description_text.value
        )
        self.assertFalse(self.page.busy or self.page.form.disabled)

    async def test_picker_and_empty_selection_validate_without_moving_files(self):
        self.assertEqual(
            [option.key for option in self.page.authors_dropdown.options],
            ["test-author"],
        )
        with patch("pages.merge_author_content.ft.FilePicker") as picker:
            picker.return_value.get_directory_path = AsyncMock(
                return_value=str(self.root)
            )
            await self.page.pick_destination_folder()
            self.assertEqual(self.page.destination_path, self.destination)
            self.assertIn("different destination", self.page.status_text.value)
            picker.return_value.get_directory_path.return_value = None
            await self.page.pick_destination_folder()
        self.page.merge_photos_check.value = self.page.merge_videos_check.value = False
        self.page.update_state()
        self.assertTrue(self.page.proceed_button.disabled)
        with patch("pages.merge_author_content.shutil.move") as move:
            await self.page.do_merge()
        move.assert_not_called()
        self.assertIn("at least one content type", self.page.description_text.value)

    async def test_leaving_finishes_current_transfer_without_starting_more(self):
        entered = asyncio.Event()
        release = threading.Event()
        self.addCleanup(release.set)
        loop = asyncio.get_running_loop()
        original_copy = shutil.copy

        def slow_copy(source, target):
            original_copy(source, target)
            loop.call_soon_threadsafe(entered.set)
            release.wait(timeout=3)

        with patch(
            "pages.merge_author_content.shutil.copy", side_effect=slow_copy
        ) as copy:
            task = asyncio.create_task(self.page.do_merge())
            await asyncio.wait_for(entered.wait(), timeout=3)
            self.page.will_unmount()
            updates = self.page.update.call_count
            release.set()
            await asyncio.wait_for(task, timeout=3)
        self.assertEqual(copy.call_count, 1)
        self.assertEqual(len(list(self.destination.iterdir())), 1)
        self.assertEqual(self.page.update.call_count, updates)
        self.assertFalse(self.page.busy)
