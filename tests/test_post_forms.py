import asyncio
import datetime
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from core.downloads_manager import DownloadManager
from pages.download_post import DownloadPostPage
from pages.download_several_posts import DownloadSeveralPostsPage
from pages.post_download_form import author_from_input

POST_ID = "dba61f8b-d6dd-4105-9d00-db1c46f13946"
POST_LINK = f"https://boosty.to/test-author/posts/{POST_ID}"


def post(identifier, timestamp, access=True):
    return SimpleNamespace(id=identifier, publish_time=timestamp, has_access=access)


def post_list(posts, last=True, offset="next"):
    return SimpleNamespace(
        data=posts, extra=SimpleNamespace(is_last=last, offset=offset)
    )


class PostFormTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager = DownloadManager()
        self.manager.add_task = AsyncMock(return_value=True)
        self.page = DownloadPostPage(self.manager)
        self.page.update = Mock()

    async def test_validation_clipboard_and_explicit_queue(self):
        for value in [
            "",
            "https://boosty.to/author",
            POST_LINK + "/media/id",
            POST_LINK + "bad",
            "https://other.site/author/posts/" + POST_ID,
        ]:
            self.page.text_field.value = value
            await self.page.download_post()
            self.assertTrue(self.page.feedback.visible)
            self.assertTrue(self.page.status_icon.color)
        self.manager.add_task.assert_not_awaited()
        with patch("pages.post_download_form.ft.Clipboard") as clipboard:
            clipboard.return_value.get = AsyncMock(return_value=" " + POST_LINK + " ")
            await self.page.paste_link()
        self.assertEqual(self.page.text_field.value, POST_LINK)
        self.manager.add_task.assert_not_awaited()
        self.assertFalse(self.page.feedback.visible)
        await self.page.download_post()
        self.manager.add_task.assert_awaited_once_with("test-author", POST_ID)
        self.assertEqual(self.page.status_text.value, "Post added to Downloads.")
        self.assertFalse(self.page.busy)
        self.manager.add_task.return_value = False
        await self.page.download_post()
        self.assertIn("already in Downloads", self.page.status_text.value)

    async def test_queue_failure_restores_form_and_folder_is_real_setting(self):
        self.page.text_field.value = POST_LINK
        self.manager.add_task.side_effect = RuntimeError("test queue failure")
        with patch("pages.download_post.logger"):
            await self.page.download_post()
        self.assertIn("Couldn't add", self.page.status_text.value)
        self.assertFalse(self.page.busy)
        self.assertFalse(self.page.progress_ring.visible)
        with patch(
            "pages.post_download_form.get_destination_folder",
            new=AsyncMock(return_value="/custom/downloads"),
        ):
            await self.page.load_destination()
        self.assertEqual(self.page.destination.value, "/custom/downloads")
        self.assertEqual(self.page.folder_note.tooltip, "/custom/downloads")


class SeveralPostsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager = DownloadManager()
        self.manager.add_task = AsyncMock(return_value=True)
        self.page = DownloadSeveralPostsPage(self.manager)
        self.page.update = Mock()
        self.page.text_field.value = "https://boosty.to/test-author/?ref=test"
        self.client = Mock()
        self.client.get_max_int_id = AsyncMock(return_value=10)
        self.client.get_posts_list = AsyncMock()
        self.auth_patch = patch(
            "pages.download_several_posts.AuthorizationProvider.get_authorization_if_valid",
            new=AsyncMock(return_value=None),
        )
        self.client_patch = patch(
            "pages.download_several_posts.BoostyClient", return_value=self.client
        )
        self.auth_patch.start()
        self.client_patch.start()
        self.addCleanup(self.auth_patch.stop)
        self.addCleanup(self.client_patch.stop)

    async def test_calendar_dates_and_inclusive_boundaries_access_and_duplicates(self):
        selected_day = datetime.date(2026, 10, 2)
        selected = datetime.datetime.combine(
            selected_day, datetime.time.min
        ).astimezone(datetime.UTC)
        self.page.handle_date_picker_change(
            SimpleNamespace(
                control=SimpleNamespace(start_value=selected, end_value=selected)
            )
        )
        self.assertEqual(self.page.parse_from.date(), selected_day)
        self.assertEqual(self.page.range_note.value, "1 day · Includes both dates")
        left = int(self.page.parse_from.timestamp())
        right = int(
            datetime.datetime.combine(
                datetime.date(2026, 10, 3), datetime.time.min
            ).timestamp()
        )
        first = post("first", left)
        last = post("last", right - 1)
        self.client.get_posts_list.side_effect = [
            post_list(
                [post("future", right), last, post("private", right - 2, False)],
                last=False,
            ),
            post_list([last, first, post("old", left - 1)], last=False, offset="older"),
        ]
        self.manager.add_task.side_effect = [True, False]
        await self.page.download_posts()
        self.assertEqual(self.client.get_posts_list.await_count, 2)
        self.client.get_posts_list.assert_any_await("test-author", offset=f"{right}:11")
        self.assertEqual(
            self.manager.add_task.await_args_list[0].args, ("test-author", "last", last)
        )
        self.assertEqual(
            self.manager.add_task.await_args_list[1].args,
            ("test-author", "first", first),
        )
        self.assertEqual(self.page.status_text.value, "1 post added to Downloads.")
        self.assertIn("1 already in Downloads", self.page.description_text.value)
        self.assertFalse(self.page.busy)
        self.assertFalse(self.page.disabled)

    async def test_empty_period_missing_author_and_network_failure_restore_form(self):
        for value in [
            "",
            "https://example.org/test-author",
            "https://boosty.to/test-author/posts/id",
            "bad author",
        ]:
            self.page.text_field.value = value
            await self.page.download_posts()
        self.client.get_max_int_id.assert_not_awaited()
        self.page.text_field.value = "test-author"
        self.client.get_max_int_id.return_value = None
        await self.page.download_posts()
        self.assertEqual(self.page.status_text.value, "No posts could be found.")
        self.client.get_max_int_id.return_value = 0
        self.client.get_posts_list.return_value = post_list([])
        await self.page.download_posts()
        self.assertEqual(
            self.page.status_text.value, "No available posts in this period."
        )
        self.client.get_posts_list.side_effect = OSError("test network error")
        with patch("pages.download_several_posts.logger"):
            await self.page.download_posts()
        self.assertEqual(
            self.page.status_text.value, "Couldn't finish preparing posts."
        )
        self.assertFalse(self.page.busy)
        self.assertFalse(self.page.progress_ring.visible)
        self.manager.add_task.assert_not_awaited()

    async def test_navigation_cancels_search_without_queuing_or_stale_updates(self):
        entered = asyncio.Event()

        async def wait_for_network(*args):
            entered.set()
            await asyncio.Event().wait()

        self.client.get_max_int_id.side_effect = wait_for_network
        task = asyncio.create_task(self.page.download_posts())
        await entered.wait()
        self.assertTrue(self.page.busy)
        self.assertFalse(self.page.disabled)
        self.page.will_unmount()
        updates = self.page.update.call_count
        await asyncio.gather(task, return_exceptions=True)
        self.assertTrue(task.cancelled())
        self.assertEqual(self.page.update.call_count, updates)
        self.manager.add_task.assert_not_awaited()

    async def test_pagination_cannot_loop_forever(self):
        self.client.get_posts_list.return_value = post_list(
            [], last=False, offset="same"
        )
        with patch("pages.download_several_posts.logger"):
            await self.page.download_posts()
        self.assertEqual(self.client.get_posts_list.await_count, 2)
        self.assertIn("Couldn't finish", self.page.status_text.value)
        self.assertFalse(self.page.busy)

    def test_author_input_supports_nickname_and_boosty_url_only(self):
        self.assertEqual(author_from_input(" test.author-1 "), "test.author-1")
        self.assertEqual(
            author_from_input("boosty.to/test-author/?ref=x"), "test-author"
        )
        self.assertIsNone(author_from_input("https://boosty.to/"))
        self.assertIsNone(author_from_input("https://other.site/test-author"))
