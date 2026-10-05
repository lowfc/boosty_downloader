import asyncio
import datetime

import flet as ft

from components.soft_layout import button_style
from core.authorization_provider import AuthorizationProvider
from core.boosty.client import BoostyClient
from core.downloads_manager import DownloadManager
from core.logger import setup_logger
from pages.post_download_form import PostDownloadForm, author_from_input, post_from_input

logger = setup_logger()


class DownloadSeveralPostsPage(PostDownloadForm):
    def __init__(self, manager: DownloadManager, localizer=None):
        super().__init__(
            manager,
            "/download-several-posts",
            "https://boosty.to/author",
            self.download_posts,
            input_validator=author_from_input,
            localizer=localizer,
        )
        today = datetime.datetime.now().astimezone().date()
        self.set_range(today - datetime.timedelta(days=2), today)
        self.date_range_picker = ft.DateRangePicker(
            start_value=self.parse_from.date(),
            end_value=self.parse_to.date(),
            entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,
            on_change=self.handle_date_picker_change,
            first_date=datetime.date(today.year - 10, 1, 1),
            last_date=today,
        )
        self.date_from_text = ft.Text(size=13)
        self.date_to_text = ft.Text(size=13)
        self.range_note = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self.update_ranges()
        dates = ft.ResponsiveRow(
            spacing=16,
            run_spacing=12,
            controls=[
                self.date_field(self.tr("From"), self.date_from_text),
                self.date_field(self.tr("To"), self.date_to_text),
            ],
        )
        self.download_button = ft.Button(
            self.tr("Download posts"),
            icon=ft.Icons.DOWNLOAD_OUTLINED,
            height=42,
            style=button_style(primary=True),
            on_click=self.download_posts,
        )
        self.build_form(
            self.tr("Several posts"),
            self.tr("Download an author's posts for a selected period."),
            ft.Icons.FILE_COPY_OUTLINED,
            self.tr("Choose an author and dates"),
            self.tr("We'll find available posts published in this period."),
            [
                self.link_section(
                    self.tr("Author"),
                    self.tr("Enter a Boosty page link or the author's nickname."),
                ),
                self.divider(),
                ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text(
                            self.tr("Publication dates"),
                            size=13,
                            weight=ft.FontWeight.W_500,
                        ),
                        dates,
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(
                                    ft.Icons.DATE_RANGE_OUTLINED,
                                    size=15,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                                self.range_note,
                            ],
                        ),
                    ],
                ),
                self.divider(),
                self.destination_section(),
                self.hint(
                    self.tr("Uses your content and quality settings."), ft.Icons.TUNE
                ),
                ft.Row(
                    wrap=True,
                    spacing=16,
                    run_spacing=10,
                    controls=[
                        self.download_button,
                        ft.Text(
                            self.tr("Progress appears in Downloads."),
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                ),
            ],
        )

    async def on_input_change(self, e=None):
        if self.active:
            post = post_from_input(self.text_field.value or "")
            if post:
                self.text_field.value = f"https://boosty.to/{post.author}"
        await super().on_input_change(e)

    def date_field(self, label, text):
        button = ft.OutlinedButton(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    text,
                    ft.Icon(
                        ft.Icons.CALENDAR_TODAY_OUTLINED,
                        size=17,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
            ),
            height=44,
            style=button_style(),
            on_click=self.open_date_picker,
            tooltip=self.tr("Choose publication dates: {label}", label=label),
        )
        self.date_buttons.append(button)
        return ft.Column(
            col={"xs": 12, "sm": 6},
            spacing=8,
            controls=[
                ft.Text(label, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                button,
            ],
        )

    def set_range(self, start, end):
        # Keep calendar dates in local time; convert to UTC only for API timestamps.
        self.parse_from = datetime.datetime.combine(start, datetime.time.min)
        self.parse_to = datetime.datetime.combine(end, datetime.time.max)

    def update_ranges(self):
        self.date_from_text.value = self.localizer.format_date(self.parse_from)
        self.date_to_text.value = self.localizer.format_date(self.parse_to)
        days = (self.parse_to.date() - self.parse_from.date()).days + 1
        self.range_note.value = self.tr(
            "{days} · Includes both dates",
            days=self.localizer.plural("count.days", days),
        )

    def open_date_picker(self, e=None):
        self.page.show_dialog(self.date_range_picker)

    def handle_date_picker_change(self, e: ft.Event[ft.DateRangePicker]):
        start, end = e.control.start_value, e.control.end_value
        if start is None or end is None:
            return
        # Flet returns local midnight encoded in UTC; recover the selected local day.
        start_day = (
            start.astimezone().date() if isinstance(start, datetime.datetime) else start
        )
        end_day = end.astimezone().date() if isinstance(end, datetime.datetime) else end
        self.set_range(start_day, end_day)
        self.update_ranges()
        self.clear_feedback()

    async def download_posts(self, e=None):
        if self.busy:
            return
        author = author_from_input(self.text_field.value or "")
        if not author:
            self.show_feedback(
                self.tr("Enter a Boosty author to continue."),
                self.tr("Use a Boosty page link or the author's nickname."),
                error=True,
            )
            return
        self.operation_task = asyncio.current_task()
        self.set_busy(True)
        self.show_feedback(
            self.tr("Searching available posts…"),
            self.tr("Checking the selected publication dates."),
            busy=True,
        )
        created = 0
        try:
            auth = await AuthorizationProvider.get_authorization_if_valid()
            client = BoostyClient(
                chunk_size=3600, download_timeout=500, auth_token=auth
            )
            max_id = await client.get_max_int_id(author)
            if max_id is None:
                self.show_feedback(
                    self.tr("No posts could be found."),
                    self.tr("Check the author link, or try again later."),
                    error=True,
                )
                return
            left = int(self.parse_from.timestamp())
            # Exclusive next midnight also handles a one-day range and DST changes.
            next_day = self.parse_to.date() + datetime.timedelta(days=1)
            right = int(
                datetime.datetime.combine(next_day, datetime.time.min).timestamp()
            )
            offset = f"{right}:{max_id + 1}"
            posts = {}
            seen_offsets = set()
            while True:
                if offset in seen_offsets:
                    raise RuntimeError("Post pagination did not advance")
                seen_offsets.add(offset)
                result = await client.get_posts_list(author, offset=offset)
                past_start = False
                for post in result.data:
                    if post.publish_time < left:
                        past_start = True
                    elif post.publish_time < right and post.has_access:
                        posts[post.id] = post
                self.show_feedback(
                    self.tr("Searching available posts…"),
                    self.localizer.plural("posts.found", len(posts)),
                    busy=True,
                )
                if result.extra.is_last or past_start:
                    break
                offset = result.extra.offset
                if not offset:
                    raise RuntimeError("Missing post pagination offset")
            if not posts:
                self.show_feedback(
                    self.tr("No available posts in this period."),
                    self.tr(
                        "Try another date range, or log in to access your subscriptions."
                    ),
                )
                return
            self.clear_input()
            self.show_feedback(
                self.localizer.plural("posts.found", len(posts)),
                self.tr("Adding posts to Downloads…"),
                busy=True,
            )
            for post in posts.values():
                if await self.manager.add_task(author, post.id, post):
                    created += 1
                self.show_feedback(
                    self.tr("Adding posts to Downloads…"),
                    self.tr("{count} tasks created", count=created),
                    busy=True,
                )
                await asyncio.sleep(0)
            skipped = len(posts) - created
            detail = self.tr("You can follow the download progress there.")
            if skipped:
                detail += self.tr(" {count} already in Downloads.", count=skipped)
            self.show_feedback(
                (
                    self.localizer.plural("posts.added", created)
                    if created
                    else self.tr("These posts are already in Downloads.")
                ),
                detail,
            )
        except Exception as error:
            logger.exception("Could not prepare author's posts", exc_info=error)
            detail = self.tr(
                "Check the author link and your connection, then try again."
            )
            if created:
                detail = self.tr(
                    "{count} posts were added to Downloads. Try again to add the remaining posts.",
                    count=created,
                )
            self.show_feedback(
                self.tr("Couldn't finish preparing posts."), detail, error=True
            )
        finally:
            self.set_busy(False)
            self.operation_task = None
            self.refresh()
