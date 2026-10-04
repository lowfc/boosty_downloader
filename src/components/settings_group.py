import asyncio
import inspect
from collections.abc import Awaitable, Callable
from pathlib import Path

import flet as ft

from components.soft_layout import button_style, soft_card, soft_icon
from components.theme_picker import ThemePicker
from core.downloads_manager import DownloadManager
from core.logger import setup_logger
from core.utils import get_download_settings
from localization import LANGUAGE_KEY, SUPPORTED_LANGUAGES, Localizer

logger = setup_logger()


@ft.control
class SettingsGroup(ft.Column):
    def __init__(
        self,
        manager: DownloadManager | None = None,
        localizer=None,
        on_language_change: Callable[[str], Awaitable[None] | None] | None = None,
    ):
        super().__init__()
        self.localizer = localizer or Localizer()
        self.tr = self.localizer.t
        self.manager = manager
        self.on_language_change = on_language_change
        self.spacing = 18
        self.loaded = self.busy = False
        self.active = True
        self.load_task = None
        self.save_lock = asyncio.Lock()
        self.pending_values = {}
        self.failed_keys = set()
        self.debounce_tasks = {}
        self.closing = False
        self.save_delay = 2
        self.host_page = None
        self.saved_values = None
        self.folder = ""
        self.theme_picker = ThemePicker(self.change_theme, localizer=self.localizer)
        self.language_dropdown = self.dropdown(
            self.tr("Language"), list(SUPPORTED_LANGUAGES.items())
        )
        self.language_dropdown.value = self.localizer.language
        self.language_dropdown.expand = True
        self.language_dropdown.text_style = ft.TextStyle(
            size=13, font_family_fallback=["LanguageFlags"]
        )
        for option in self.language_dropdown.options:
            option.content = ft.Text(
                option.text, size=13, font_family_fallback=["LanguageFlags"]
            )
        self.current_download_folder_text = ft.Text(
            self.tr("Loading download folder…"), size=13, expand=True
        )
        self.folder_button = ft.OutlinedButton(
            self.tr("Change"),
            height=38,
            style=button_style(),
            on_click=self.pick_download_folder,
        )
        self.switch_download_photos = self.content_switch(self.tr("Download photos"))
        self.switch_download_videos = self.content_switch(self.tr("Download videos"))
        self.switch_download_audios = self.content_switch(self.tr("Download audio"))
        self.switch_download_files = self.content_switch(
            self.tr("Download attached files")
        )
        self.switches = [
            self.switch_download_photos,
            self.switch_download_videos,
            self.switch_download_audios,
            self.switch_download_files,
        ]
        self.video_size_dropdown = self.dropdown(
            self.tr("Video quality limit"),
            [
                ("low", self.tr("Low")),
                ("medium", self.tr("Medium")),
                ("high", self.tr("High")),
                ("full_hd", self.tr("Full HD")),
                ("ultra_hd", self.tr("No limit")),
            ],
        )
        self.post_text_format_dropdown = self.dropdown(
            self.tr("Post text format"),
            [("md", self.tr("Markdown (.md)")), ("raw", self.tr("Plain text (.txt)"))],
        )
        self.chunk_size_textfield = self.number_field(self.tr("Chunk size (bytes)"))
        self.download_timeout_textfield = self.number_field(
            self.tr("Download timeout (seconds)")
        )
        self.max_parallelism_textfield = self.number_field(
            self.tr("Simultaneous downloads")
        )
        self.max_parallelism_textfield.width = 90
        self.numeric_fields = [
            (self.chunk_size_textfield, 1500, 500000),
            (self.download_timeout_textfield, 100, 1000000),
            (self.max_parallelism_textfield, 1, 30),
        ]
        self.advanced_fields = ft.Container(
            visible=False,
            padding=ft.Padding.only(top=18),
            content=ft.ResponsiveRow(
                spacing=20,
                run_spacing=18,
                controls=[
                    self.field_column(
                        self.tr("Chunk size (bytes)"),
                        self.chunk_size_textfield,
                        self.tr("Data read in a single chunk."),
                    ),
                    self.field_column(
                        self.tr("Download timeout (seconds)"),
                        self.download_timeout_textfield,
                        self.tr("How long to wait for a response."),
                    ),
                ],
            ),
        )
        self.advanced_button = ft.TextButton(
            self.tr("Advanced settings"),
            icon=ft.Icons.EXPAND_MORE,
            height=38,
            style=ft.ButtonStyle(
                color=ft.Colors.ON_SURFACE_VARIANT,
                padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                shape=ft.RoundedRectangleBorder(radius=8),
                text_style=ft.TextStyle(size=13),
            ),
            on_click=self.toggle_advanced,
        )
        self.general_card = self.card(
            ft.Icons.TUNE,
            self.tr("General"),
            self.tr("Your download folder and app appearance."),
            [
                ft.Column(
                    spacing=9,
                    controls=[
                        self.label(self.tr("Download folder")),
                        ft.Container(
                            bgcolor=ft.Colors.SURFACE,
                            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                            border_radius=10,
                            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
                            content=ft.Row(
                                spacing=14,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.FOLDER_OUTLINED,
                                        size=20,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                    self.current_download_folder_text,
                                    self.folder_button,
                                ],
                            ),
                        ),
                    ],
                ),
                self.divider(),
                ft.Column(
                    spacing=9,
                    controls=[self.label(self.tr("App theme")), self.theme_picker],
                ),
                self.divider(),
                ft.Column(
                    spacing=9,
                    controls=[
                        self.label(self.tr("Language")),
                        ft.Row(
                            spacing=10,
                            controls=[
                                self.language_dropdown,
                                ft.Container(expand=True),
                                ft.Container(expand=True),
                            ],
                        ),
                        self.hint(self.tr("Changes are saved automatically.")),
                    ],
                ),
            ],
        )
        switch_rows = []
        for icon, title, detail, switch in [
            (
                ft.Icons.IMAGE_OUTLINED,
                self.tr("Photos"),
                self.tr("Images and photo collections"),
                self.switch_download_photos,
            ),
            (
                ft.Icons.VIDEOCAM_OUTLINED,
                self.tr("Videos"),
                self.tr("Video posts and clips"),
                self.switch_download_videos,
            ),
            (
                ft.Icons.MUSIC_NOTE_OUTLINED,
                self.tr("Audio"),
                self.tr("Audio tracks and recordings"),
                self.switch_download_audios,
            ),
            (
                ft.Icons.INSERT_DRIVE_FILE_OUTLINED,
                self.tr("Attached files"),
                self.tr("Documents, archives and other files"),
                self.switch_download_files,
            ),
        ]:
            if switch_rows:
                switch_rows.append(self.divider())
            switch_rows.append(
                ft.Container(
                    padding=ft.Padding.symmetric(vertical=10),
                    content=ft.Row(
                        spacing=12,
                        controls=[
                            ft.Icon(icon, size=18, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Column(
                                expand=True,
                                spacing=3,
                                controls=[self.label(title), self.hint(detail)],
                            ),
                            switch,
                        ],
                    ),
                )
            )
        self.content_card = self.card(
            ft.Icons.LAYERS_OUTLINED,
            self.tr("Content"),
            self.tr("Choose what to download from each post."),
            [
                ft.Column(spacing=0, controls=switch_rows),
                self.divider(),
                ft.ResponsiveRow(
                    spacing=20,
                    run_spacing=18,
                    controls=[
                        self.field_column(
                            self.tr("Video quality limit"),
                            self.video_size_dropdown,
                            self.tr("Maximum quality to download."),
                        ),
                        self.field_column(
                            self.tr("Post text format"),
                            self.post_text_format_dropdown,
                            self.tr("How the post's text is saved."),
                        ),
                    ],
                ),
            ],
        )
        self.downloads_card = self.card(
            ft.Icons.DOWNLOAD_OUTLINED,
            self.tr("Downloads"),
            self.tr("Control how your downloads run."),
            [
                ft.Row(
                    spacing=20,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=4,
                            controls=[
                                self.label(self.tr("Simultaneous downloads")),
                                self.hint(
                                    self.tr(
                                        "Number of posts downloaded at the same time."
                                    )
                                ),
                            ],
                        ),
                        self.max_parallelism_textfield,
                    ],
                ),
                self.divider(),
                ft.Column(
                    spacing=0, controls=[self.advanced_button, self.advanced_fields]
                ),
            ],
        )
        self.status_text = ft.Text(
            self.tr("Loading settings…"),
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            expand=True,
            text_align=ft.TextAlign.RIGHT,
        )
        self.retry_button = ft.TextButton(
            self.tr("Retry"),
            icon=ft.Icons.REFRESH,
            on_click=self.flush_pending_saves,
            visible=False,
        )
        self.controls = [
            self.general_card,
            self.content_card,
            self.downloads_card,
            ft.Container(
                padding=ft.Padding.only(top=6),
                content=ft.Row(
                    spacing=16, controls=[self.status_text, self.retry_button]
                ),
            ),
        ]
        self.setting_controls = {
            "download-folder": self.folder_button,
            "current-app-theme": self.theme_picker,
            LANGUAGE_KEY: self.language_dropdown,
            "need-download-photos": self.switch_download_photos,
            "need-download-videos": self.switch_download_videos,
            "need-download-audios": self.switch_download_audios,
            "need-download-files": self.switch_download_files,
            "download-chunk-size": self.chunk_size_textfield,
            "download-timeout": self.download_timeout_textfield,
            "download-max-parallelism": self.max_parallelism_textfield,
            "post-text-format": self.post_text_format_dropdown,
            "preferred-video-size": self.video_size_dropdown,
        }
        self.set_editing_enabled(False)

    @staticmethod
    def label(value):
        return ft.Text(value, size=13, weight=ft.FontWeight.W_500)

    @staticmethod
    def hint(value):
        return ft.Text(value, size=12, color=ft.Colors.ON_SURFACE_VARIANT)

    @staticmethod
    def divider():
        return ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT)

    def card(self, icon, title, subtitle, controls):
        return soft_card(
            ft.Column(
                spacing=24,
                controls=[
                    ft.Row(
                        spacing=14,
                        controls=[
                            soft_icon(icon),
                            ft.Column(
                                expand=True,
                                spacing=3,
                                controls=[
                                    ft.Text(title, size=15, weight=ft.FontWeight.W_500),
                                    self.hint(subtitle),
                                ],
                            ),
                        ],
                    ),
                    *controls,
                ],
            ),
            padding=26,
        )

    def field_column(self, title, control, helper):
        return ft.Column(
            col={"xs": 12, "sm": 6},
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=9,
            controls=[self.label(title), control, self.hint(helper)],
        )

    def content_switch(self, label):
        return ft.Switch(
            value=True,
            tooltip=label,
            on_change=self.save_control,
            active_color=ft.Colors.ON_PRIMARY,
            active_track_color=ft.Colors.PRIMARY,
            track_outline_width=0,
            mouse_cursor=ft.MouseCursor.CLICK,
        )

    def dropdown(self, label, options):
        return ft.Dropdown(
            expanded_insets=ft.Padding.all(0),
            value=options[-1][0],
            tooltip=label,
            text_size=13,
            dense=True,
            filled=True,
            fill_color=ft.Colors.SURFACE,
            border=ft.OutlineInputBorder(
                side=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT), border_radius=9
            ),
            options=[ft.DropdownOption(key=key, text=text) for key, text in options],
            on_select=self.save_control,
        )

    def number_field(self, label):
        return ft.TextField(
            value="",
            tooltip=label,
            error_style=ft.TextStyle(size=11),
            error_max_lines=2,
            text_size=13,
            dense=True,
            filled=True,
            fill_color=ft.Colors.SURFACE,
            border=ft.OutlineInputBorder(
                side=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT), border_radius=9
            ),
            input_filter=ft.NumbersOnlyInputFilter(),
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self.schedule_text_save,
        )

    def refresh(self):
        if self.active:
            self.update()

    def set_editing_enabled(self, enabled):
        self.language_dropdown.disabled = not enabled
        self.folder_button.disabled = self.advanced_button.disabled = not enabled
        for button in self.theme_picker.buttons.values():
            button.disabled = not enabled
        for switch in self.switches:
            switch.disabled = not enabled
        for field, _, _ in self.numeric_fields:
            field.read_only = not enabled
        self.post_text_format_dropdown.disabled = not enabled
        self.video_size_dropdown.disabled = (
            not enabled or not self.switch_download_videos.value
        )

    def draft_values(self):
        return {
            "download-folder": self.folder,
            "current-app-theme": self.theme_picker.value,
            LANGUAGE_KEY: self.language_dropdown.value,
            "need-download-photos": str(self.switch_download_photos.value),
            "need-download-videos": str(self.switch_download_videos.value),
            "need-download-audios": str(self.switch_download_audios.value),
            "need-download-files": str(self.switch_download_files.value),
            "download-chunk-size": self.chunk_size_textfield.value,
            "download-timeout": self.download_timeout_textfield.value,
            "download-max-parallelism": self.max_parallelism_textfield.value,
            "post-text-format": self.post_text_format_dropdown.value,
            "preferred-video-size": self.video_size_dropdown.value,
        }

    def status(self, message, error=False):
        self.status_text.value = message
        self.status_text.color = (
            ft.Colors.ERROR if error else ft.Colors.ON_SURFACE_VARIANT
        )

    def queue_change(self, key):
        if not self.loaded or not self.active or self.closing:
            return False
        value = self.draft_values()[key]
        # Keep even a reverted value while a write is in progress: it must follow
        # the in-flight write rather than disappear against the old saved value.
        if value == self.saved_values[key] and not self.busy:
            self.pending_values.pop(key, None)
            self.failed_keys.discard(key)
        else:
            self.pending_values[key] = value
        self.video_size_dropdown.disabled = not self.switch_download_videos.value
        self.retry_button.visible = bool(self.failed_keys)
        self.status(
            (
                self.tr("Couldn't save settings. Please try again.")
                if self.failed_keys
                else (
                    self.tr("Waiting to save…")
                    if self.pending_values
                    else self.tr("Changes saved.")
                )
            ),
            error=bool(self.failed_keys),
        )
        self.refresh()
        return True

    def key_for_control(self, control):
        return next(
            key for key, item in self.setting_controls.items() if item is control
        )

    async def save_control(self, e):
        key = self.key_for_control(e.control)
        if self.queue_change(key):
            await self.save_pending([key])

    async def change_theme(self, value):
        if self.queue_change("current-app-theme"):
            await self.save_pending(["current-app-theme"])

    def schedule_text_save(self, e):
        key = self.key_for_control(e.control)
        e.control.error = None
        if not self.queue_change(key):
            return
        task = self.debounce_tasks.pop(key, None)
        if task:
            task.cancel()
        if key in self.pending_values:
            self.debounce_tasks[key] = asyncio.create_task(self.delayed_save(key))

    async def delayed_save(self, key):
        await asyncio.sleep(self.save_delay)
        # Once persistence starts, typing may schedule another timer but must
        # never cancel a partially completed write.
        self.debounce_tasks.pop(key, None)
        await self.save_pending([key])

    async def flush_pending_saves(self, e=None):
        tasks = list(self.debounce_tasks.values())
        self.debounce_tasks.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await self.save_pending(list(self.pending_values))

    def toggle_advanced(self, e=None):
        self.advanced_fields.visible = not self.advanced_fields.visible
        self.advanced_button.icon = (
            ft.Icons.EXPAND_LESS
            if self.advanced_fields.visible
            else ft.Icons.EXPAND_MORE
        )
        self.refresh()

    def show_folder(self):
        home = str(Path.home())
        self.current_download_folder_text.value = (
            "~" + self.folder[len(home) :]
            if self.folder.startswith(home + "/")
            else self.folder
        )
        self.current_download_folder_text.tooltip = self.folder

    async def pick_download_folder(self, e=None):
        if not self.loaded or self.closing:
            return
        try:
            path = await ft.FilePicker().get_directory_path(
                initial_directory=self.folder
            )
            if path and self.active:
                self.folder = path
                self.show_folder()
                if self.queue_change("download-folder"):
                    await self.save_pending(["download-folder"])
        except Exception:
            logger.exception("Could not select download folder")
            self.status(
                self.tr("Couldn't choose a folder. Please try again."), error=True
            )
            self.refresh()

    def did_mount(self):
        self.host_page = self.page
        self.load_task = asyncio.create_task(self.set_initial_values())

    def will_unmount(self):
        self.active = False
        if self.load_task and not self.load_task.done():
            self.load_task.cancel()
        if self.pending_values or self.debounce_tasks:
            asyncio.create_task(self.flush_pending_saves())

    async def set_initial_values(self):
        try:
            settings = await get_download_settings()
            if settings is None:
                raise ValueError("Download settings are unavailable")
            mode = await ft.SharedPreferences().get("current-app-theme") or "system"
            self.folder = settings.downloads_folder
            self.show_folder()
            self.theme_picker.set_value(mode)
            self.language_dropdown.value = self.localizer.language
            self.switch_download_photos.value = settings.need_download_photos
            self.switch_download_videos.value = settings.need_download_videos
            self.switch_download_audios.value = settings.need_download_audios
            self.switch_download_files.value = settings.need_download_files
            self.chunk_size_textfield.value = str(settings.chunk_size)
            self.download_timeout_textfield.value = str(settings.download_timeout)
            self.max_parallelism_textfield.value = str(settings.max_parallelism)
            self.video_size_dropdown.value = (
                settings.preferred_video_size
                if settings.preferred_video_size
                in ("low", "medium", "high", "full_hd", "ultra_hd")
                else "ultra_hd"
            )
            self.post_text_format_dropdown.value = (
                settings.post_text_format
                if settings.post_text_format in ("md", "raw")
                else "raw"
            )
            self.saved_values = self.draft_values()
            self.loaded = True
            self.set_editing_enabled(True)
            self.status(self.tr("Changes are saved automatically."))
        except Exception:
            logger.exception("Could not load settings")
            self.status(
                self.tr("Couldn't load settings. Reopen this page to try again."),
                error=True,
            )
        self.refresh()

    def validated_value(self, key, value):
        control = self.setting_controls[key]
        for field, minimum, maximum in self.numeric_fields:
            if control is not field:
                continue
            try:
                number = int(value)
                valid = minimum <= number <= maximum
            except (TypeError, ValueError):
                valid = False
            field.error = None if valid else f"{minimum:,}–{maximum:,}"
            if valid:
                return str(number)
            if field is not self.max_parallelism_textfield:
                self.advanced_fields.visible = True
                self.advanced_button.icon = ft.Icons.EXPAND_LESS
            return None
        if key == LANGUAGE_KEY and value not in SUPPORTED_LANGUAGES:
            return None
        if key == "download-folder" and not value:
            return None
        return value

    async def save_pending(self, keys):
        language_changed = False
        invalid = False
        async with self.save_lock:
            self.busy = True
            try:
                preferences = ft.SharedPreferences()
                for key in keys:
                    if key not in self.pending_values:
                        continue
                    draft = self.pending_values[key]
                    value = self.validated_value(key, draft)
                    if value is None:
                        invalid = True
                        continue
                    if value != self.saved_values[key]:
                        self.status(self.tr("Saving changes…"))
                        self.refresh()
                        previous = None
                        attempted = False
                        try:
                            previous = await preferences.get(key)
                            attempted = True
                            if await preferences.set(key, value) is False:
                                raise OSError(f"Could not save setting {key}")
                            if key == "download-max-parallelism" and self.manager:
                                await self.manager.set_maximum_concurrency(int(value))
                        except Exception:
                            logger.exception("Could not save setting %s", key)
                            self.failed_keys.add(key)
                            if attempted:
                                try:
                                    restored = (
                                        await preferences.remove(key)
                                        if previous is None
                                        else await preferences.set(key, previous)
                                    )
                                    if restored is False:
                                        raise OSError(
                                            f"Could not restore setting {key}"
                                        )
                                except Exception:
                                    logger.exception(
                                        "Could not restore setting %s", key
                                    )
                            continue
                        self.saved_values[key] = value
                    self.failed_keys.discard(key)
                    if self.pending_values.get(key) == draft:
                        self.pending_values.pop(key, None)
                        control = self.setting_controls[key]
                        if isinstance(control, ft.TextField):
                            control.value = value
                    if key == "current-app-theme" and self.host_page:
                        self.host_page.theme_mode = ft.ThemeMode(value)
                        try:
                            self.host_page.update()
                        except Exception:
                            logger.exception("Could not refresh the saved theme")
                    if key == LANGUAGE_KEY:
                        language_changed = value != self.localizer.language
                        self.localizer.set_language(value)
                        if self.host_page:
                            self.localizer.configure_page(self.host_page)
            finally:
                self.busy = False
                self.retry_button.visible = bool(self.failed_keys)
                if self.failed_keys:
                    self.status(
                        self.tr("Couldn't save settings. Please try again."), error=True
                    )
                elif invalid or any(field.error for field, _, _ in self.numeric_fields):
                    self.status(self.tr("Check the highlighted settings."), error=True)
                else:
                    self.status(
                        self.tr("Waiting to save…")
                        if self.pending_values
                        else self.tr("Changes saved.")
                    )
                self.refresh()
        if (
            language_changed
            and self.active
            and not self.closing
            and self.on_language_change
        ):
            result = self.on_language_change(self.localizer.language)
            if inspect.isawaitable(result):
                await result
