import asyncio

import flet as ft

import __version__ as app_version
import components


@ft.control
class SettingsGroup(ft.ListView):
    def __init__(self):
        super().__init__()
        self.align = ft.Alignment.CENTER
        self.expand = True
        self.spacing = 10
        self.padding = 5
        self.width = 700
        self.disabled = True

        self.current_download_folder_text = ft.Text(value="Fetching...", size=20, color=ft.Colors.ON_SURFACE_VARIANT)
        self.switch_download_photos = ft.Switch(label="Download photos", value=True, padding=10)
        self.switch_download_videos = ft.Switch(label="Download videos", value=True, padding=10)
        self.switch_download_audios = ft.Switch(label="Download audios", value=True, padding=10)
        self.switch_download_files = ft.Switch(label="Download attached files", value=True, padding=10)
        self.media_size_dropdown = ft.Dropdown(
            width=700,
            value="max",
            label="Preferred media size",
            border_color=ft.Colors.TRANSPARENT,
            filled=True,
            fill_color=ft.Colors.SURFACE_CONTAINER,
            options=[
                ft.DropdownOption(key="low", text="Low"),
                ft.DropdownOption(key="medium", text="Medium"),
                ft.DropdownOption(key="high", text="High"),
                ft.DropdownOption(key="full_hd", text="Full HD"),
                ft.DropdownOption(key="ultra_hd", text="Ultra HD"),
                ft.DropdownOption(key="max", text="Max available"),
            ],
        )
        self.post_text_format_dropdown = ft.Dropdown(
            width=700,
            value="md",
            label="Post text format",
            border_color=ft.Colors.TRANSPARENT,
            filled=True,
            fill_color=ft.Colors.SURFACE_CONTAINER,
            options=[
                ft.DropdownOption(key="md", text="Markdown file (.md)"),
                ft.DropdownOption(key="raw", text="Text file (.txt)"),
            ],
        )
        self.chunk_size_textfield = ft.TextField(
            label="Chunk size", border=ft.InputBorder.UNDERLINE,
            input_filter=ft.NumbersOnlyInputFilter(),
            value="0"
        )
        self.download_timeout_textfield = ft.TextField(
            label="Download timeout (sec.)",
            border=ft.InputBorder.UNDERLINE,
            input_filter=ft.NumbersOnlyInputFilter(),
            value="0"
        )
        self.max_parallelism_textfield = ft.TextField(
            label="Maximum download parallelism",
            border=ft.InputBorder.UNDERLINE,
            input_filter=ft.NumbersOnlyInputFilter(),
            value="0"
        )
        self.controls = [
            ft.Text(
                spans=[
                    ft.TextSpan(
                        f"{app_version.NAME} {app_version.VERSION} [{app_version.PLATFORM}]",
                        ft.TextStyle(weight=ft.FontWeight.BOLD, size=25, color=ft.Colors.ON_SURFACE),
                        url=app_version.URL
                    )
                ]
            ),
            ft.Text("Download folder", theme_style=ft.TextThemeStyle.LABEL_MEDIUM),
            ft.Button(
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
                content=ft.Container(
                    height=50,
                    padding=ft.Padding.all(5),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.FOLDER, size=20, color=ft.Colors.ON_SURFACE_VARIANT),
                            self.current_download_folder_text
                        ],
                    ),
                ),
                on_click=lambda e: asyncio.create_task(self.pick_download_folder())
            ),
            ft.Text("App theme", theme_style=ft.TextThemeStyle.LABEL_MEDIUM),
            components.ThemePicker(),
            ft.Text("Content settings", theme_style=ft.TextThemeStyle.LABEL_MEDIUM),
            self.switch_download_photos,
            self.switch_download_videos,
            self.switch_download_audios,
            self.switch_download_files,
            ft.Column(
                spacing=25,
                controls=[
                    self.media_size_dropdown,
                    self.post_text_format_dropdown,
                ]
            ),
            ft.Text("Download settings", theme_style=ft.TextThemeStyle.LABEL_MEDIUM),
            self.chunk_size_textfield,
            self.download_timeout_textfield,
            self.max_parallelism_textfield,
            ft.FilledButton("Save", height=50, margin=15, on_click=lambda e: asyncio.create_task(self.apply_settings())),
        ]

        asyncio.create_task(self.set_initial_values())

    async def pick_download_folder(self):
        path = await ft.FilePicker().get_directory_path()
        if path:
            await ft.SharedPreferences().set("download-folder", path)
            self.current_download_folder_text.value = path
            self.page.update()

    async def apply_settings(self):
        new_chunk_size = self.chunk_size_textfield.value
        if not new_chunk_size or 500000 < int(new_chunk_size) < 10000:
            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Chunk size"),
                    content=ft.Text("Please enter value between 10000 and 500000."),
                    actions=[ft.TextButton("Understand", on_click=lambda e: self.page.pop_dialog())],
                    open=True,
                )
            )
            return

        new_download_timeout = self.download_timeout_textfield.value
        if not new_download_timeout or int(new_download_timeout) < 10:
            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Download timeout (sec.)"),
                    content=ft.Text("Not recommended to set timeout less, than 10 seconds."),
                    actions=[ft.TextButton("Understand", on_click=lambda e: self.page.pop_dialog())],
                    open=True,
                )
            )
            return

        new_max_parallelism = self.max_parallelism_textfield.value
        if not new_max_parallelism or 10 < int(new_max_parallelism) < 1:
            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Maximum download parallelism"),
                    content=ft.Text("Please enter value between 1 and 10."),
                    actions=[ft.TextButton("Understand", on_click=lambda e: self.page.pop_dialog())],
                    open=True,
                )
            )
            return

        await ft.SharedPreferences().set("need-download-photos", str(self.switch_download_photos.value))
        await ft.SharedPreferences().set("need-download-videos", str(self.switch_download_videos.value))
        await ft.SharedPreferences().set("need-download-audios", str(self.switch_download_audios.value))
        await ft.SharedPreferences().set("need-download-files", str(self.switch_download_files.value))

        await ft.SharedPreferences().set("download-chunk-size", str(new_chunk_size))
        await ft.SharedPreferences().set("download-timeout", str(new_download_timeout))
        await ft.SharedPreferences().set("download-max-parallelism", str(new_max_parallelism))

        self.page.show_dialog(ft.SnackBar(ft.Text("Saved")))

    async def set_initial_values(self):
        initial_download_photos = await ft.SharedPreferences().get("need-download-photos") == "True"
        if initial_download_photos is None:
            initial_download_photos = True
        initial_download_videos = await ft.SharedPreferences().get("need-download-videos") == "True"
        if initial_download_videos is None:
            initial_download_videos = True
        initial_download_audios = await ft.SharedPreferences().get("need-download-audios") == "True"
        if initial_download_audios is None:
            initial_download_audios = True
        initial_download_files = await ft.SharedPreferences().get("need-download-files") == "True"
        if initial_download_files is None:
            initial_download_files = True

        initial_chunk_size = int(await ft.SharedPreferences().get("download-chunk-size") or 153600)
        initial_download_timeout = int(await ft.SharedPreferences().get("download-timeout") or 3600)
        initial_max_parallelism = int(await ft.SharedPreferences().get("download-max-parallelism") or 5)
        initial_download_folder = await ft.SharedPreferences().get("download-folder") or r"C:\boosty_dumps"

        self.switch_download_photos.value = initial_download_photos
        self.switch_download_videos.value = initial_download_videos
        self.switch_download_audios.value = initial_download_audios
        self.switch_download_files.value = initial_download_files
        self.chunk_size_textfield.value = initial_chunk_size
        self.download_timeout_textfield.value = initial_download_timeout
        self.max_parallelism_textfield.value = initial_max_parallelism
        self.current_download_folder_text.value = initial_download_folder
        self.disabled = False
        self.page.update()