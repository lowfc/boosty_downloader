import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch

import flet as ft

from core.downloads_manager import DownloadManager
from pages.download_image_by_link import DownloadImageByLinkPage
from pages.download_post import DownloadPostPage
from pages.download_several_posts import DownloadSeveralPostsPage

POST_ID = "dba61f8b-d6dd-4105-9d00-db1c46f13946"
POST_LINK = f"https://boosty.to/test-author/posts/{POST_ID}"
IMAGE_LINK = f"{POST_LINK}/media/9b981067-9854-4af0-aed4-6b5efe3ad96f"


class InputValidationTests(unittest.IsolatedAsyncioTestCase):
    def make_page(self, page_type=DownloadPostPage):
        page = page_type(DownloadManager())
        page.update = Mock()
        self.addCleanup(page.will_unmount)
        return page

    async def test_all_three_fields_validate_after_half_second_without_downloading(
        self,
    ):
        cases = [
            (DownloadPostPage, POST_LINK, POST_LINK + "bad"),
            (DownloadSeveralPostsPage, "test-author", "bad author"),
            (
                DownloadSeveralPostsPage,
                "https://boosty.to/test-author",
                "https://other.site/author",
            ),
            (DownloadImageByLinkPage, IMAGE_LINK, POST_LINK),
        ]
        for page_type, valid, invalid in cases:
            with self.subTest(page=page_type.__name__, value=valid):
                page = self.make_page(page_type)
                page.manager.add_task = AsyncMock()
                with patch(
                    "pages.post_download_form.asyncio.sleep", new=AsyncMock()
                ) as delay:
                    page.text_field.value = valid
                    await page.text_field.on_change(None)
                    self.assertFalse(page.input_valid_icon.visible)
                    await page.validation_task
                    self.assertTrue(page.input_valid_icon.visible)
                    delay.assert_awaited_once_with(0.5)
                    self.assertEqual(
                        page.input_valid_icon.content.color, ft.Colors.WHITE
                    )
                    self.assertEqual(page.input_valid_icon.bgcolor, ft.Colors.GREEN_600)
                    page.text_field.value = invalid
                    await page.text_field.on_change(None)
                    self.assertFalse(page.input_valid_icon.visible)
                    await page.validation_task
                    self.assertFalse(page.input_valid_icon.visible)
                    page.text_field.value = ""
                    await page.text_field.on_change(None)
                    self.assertIsNone(page.validation_task)
                page.manager.add_task.assert_not_awaited()
                self.assertIsNone(page.operation_task)

    async def test_typing_restarts_delay_and_cancels_previous_validation(self):
        page = self.make_page()
        entered = asyncio.Queue()
        release = asyncio.Event()
        real_sleep = asyncio.sleep

        async def wait(seconds):
            entered.put_nowait(seconds)
            await release.wait()

        with patch("pages.post_download_form.asyncio.sleep", side_effect=wait):
            page.text_field.value = POST_LINK
            await page.on_input_change()
            self.assertEqual(await entered.get(), 0.5)
            first = page.validation_task
            page.text_field.value = POST_LINK + "bad"
            await page.on_input_change()
            self.assertEqual(await entered.get(), 0.5)
            self.assertTrue(first.cancelled())
            self.assertFalse(page.input_valid_icon.visible)
            release.set()
            await page.validation_task
            self.assertFalse(page.input_valid_icon.visible)
            await real_sleep(0)

    async def test_paste_schedules_validation_and_clearing_cancels_it(self):
        page = self.make_page()
        with patch("pages.post_download_form.ft.Clipboard") as clipboard:
            clipboard.return_value.get = AsyncMock(return_value=" " + POST_LINK + " ")
            await page.paste_link()
        self.assertFalse(page.input_valid_icon.visible)
        pending = page.validation_task
        page.clear_input()
        await asyncio.gather(pending, return_exceptions=True)
        self.assertTrue(pending.cancelled())
        self.assertEqual(page.text_field.value, "")
        self.assertFalse(page.input_valid_icon.visible)

    async def test_author_field_converts_post_links_from_both_paste_paths(self):
        links = [
            POST_LINK,
            POST_LINK + "?share=post_link",
            " https://boosty.to/test-author/posts/"
            "cf0289f5-1d3c-4966-ad8d-3f8fb17fb105/?share=post_link#post ",
        ]
        for use_button in (False, True):
            for link in links:
                with self.subTest(button=use_button, link=link):
                    page = self.make_page(DownloadSeveralPostsPage)
                    page.manager.add_task = AsyncMock()
                    with patch(
                        "pages.post_download_form.asyncio.sleep", new=AsyncMock()
                    ):
                        if use_button:
                            with patch(
                                "pages.post_download_form.ft.Clipboard"
                            ) as clipboard:
                                clipboard.return_value.get = AsyncMock(
                                    return_value=link
                                )
                                await page.paste_button.on_click(None)
                        else:
                            page.text_field.value = link
                            await page.text_field.on_change(None)
                        self.assertEqual(
                            page.text_field.value, "https://boosty.to/test-author"
                        )
                        await page.validation_task
                    self.assertTrue(page.input_valid_icon.visible)
                    page.manager.add_task.assert_not_awaited()
                    self.assertIsNone(page.operation_task)

    async def test_author_field_keeps_other_input_unchanged(self):
        values = [
            "test-author",
            "https://boosty.to/test-author/?ref=test",
            POST_LINK.replace("boosty.to", "other.site"),
            POST_LINK + "bad",
            IMAGE_LINK,
            "https://boosty.to/",
        ]
        for value in values:
            with self.subTest(value=value):
                page = self.make_page(DownloadSeveralPostsPage)
                page.text_field.value = value
                with patch("pages.post_download_form.asyncio.sleep", new=AsyncMock()):
                    await page.text_field.on_change(None)
                    await page.validation_task
                self.assertEqual(page.text_field.value, value)
        page = self.make_page(DownloadPostPage)
        page.text_field.value = POST_LINK + "?share=post_link"
        with patch("pages.post_download_form.asyncio.sleep", new=AsyncMock()):
            await page.text_field.on_change(None)
            await page.validation_task
        self.assertEqual(page.text_field.value, POST_LINK + "?share=post_link")
        self.assertTrue(page.input_valid_icon.visible)

    async def test_leaving_page_cancels_validation_without_stale_updates(self):
        page = self.make_page()
        page.text_field.value = POST_LINK
        await page.on_input_change()
        pending = page.validation_task
        updates = page.update.call_count
        page.will_unmount()
        await asyncio.gather(pending, return_exceptions=True)
        self.assertTrue(pending.cancelled())
        self.assertFalse(page.input_valid_icon.visible)
        self.assertEqual(page.update.call_count, updates)
