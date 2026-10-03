import asyncio
import datetime
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from components.app_bar import AppBar


class AppBarTests(unittest.IsolatedAsyncioTestCase):
    async def test_expired_login_and_empty_download_queue_refresh_status(self):
        manager = SimpleNamespace(total_tasks=2)
        changes = Mock()
        toolbar = AppBar(manager, on_auth_change=changes)
        snapshots = []
        toolbar.update = lambda: snapshots.append(
            (
                toolbar.status_text.value,
                toolbar.login_button.content,
                (
                    toolbar.downloads_button.badge.label
                    if toolbar.downloads_button.badge
                    else None
                ),
            )
        )
        now = datetime.datetime.now(datetime.UTC)
        expires = [
            now + datetime.timedelta(days=1),
            now - datetime.timedelta(seconds=1),
            None,
        ]
        pauses = 0

        async def next_tick(_):
            nonlocal pauses
            pauses += 1
            manager.total_tasks = 0
            if pauses == 3:
                raise asyncio.CancelledError

        with (
            patch(
                "components.app_bar.AuthorizationProvider.get_token_valid_to",
                new=AsyncMock(side_effect=expires),
            ),
            patch("components.app_bar.asyncio.sleep", side_effect=next_tick),
            self.assertRaises(asyncio.CancelledError),
        ):
            await toolbar.update_task()

        self.assertEqual(
            snapshots,
            [
                ("Logged in", "Account", "2"),
                ("Not logged in", "Log in", None),
                ("Not logged in", "Log in", None),
            ],
        )
        self.assertEqual(
            [call.args[0] for call in changes.call_args_list], [True, False]
        )
