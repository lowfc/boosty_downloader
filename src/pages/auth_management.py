import asyncio
import datetime
from pathlib import Path

import aiofiles
import flet as ft

import components
from components.soft_layout import button_style, page_shell, soft_card, soft_icon
from core.authorization_provider import AuthorizationProvider
from core.downloads_manager import DownloadManager


class AuthManagementPage(ft.View):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.route = "/auth-management"
        self.padding = 0
        self.spacing = 0
        self.refresh_task = None
        self.copy_task = None
        self.title = ft.Text("Log in", size=24, weight=ft.FontWeight.W_500)
        self.subtitle = ft.Text(
            "Connect your Boosty account to access your subscriptions.",
            size=13,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self.copy_script_button = ft.OutlinedButton(
            "Copy script",
            icon=ft.Icons.CONTENT_COPY,
            style=button_style(),
            height=40,
            on_click=self.copy_script,
        )
        self.script_error = ft.Text("", size=12, color=ft.Colors.ERROR, visible=False)
        self.instructions = ft.Container(
            visible=False,
            padding=ft.Padding.only(top=8),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text(text, size=12, color=ft.Colors.ON_SURFACE_VARIANT)
                    for text in [
                        "1. Open boosty.to in your browser and log in to your existing account.",
                        "2. Open Developer Tools and select Console (⌥⌘J on Chrome for Mac, Ctrl+Shift+J on Windows).",
                        "3. Paste the copied script and run it. If the browser asks you to allow pasting, follow its instructions.",
                        "4. Copy the token returned by the script and paste it below.",
                    ]
                ],
            ),
        )
        self.instructions_button = ft.TextButton(
            "Show browser instructions",
            height=36,
            icon=ft.Icons.KEYBOARD_ARROW_DOWN,
            on_click=self.toggle_instructions,
            style=ft.ButtonStyle(
                color=ft.Colors.ON_SURFACE_VARIANT,
                padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                shape=ft.RoundedRectangleBorder(radius=8),
                text_style=ft.TextStyle(size=12),
            ),
        )
        self.token_text_field = ft.TextField(
            value="",
            hint_text="Paste your Boosty token",
            password=True,
            can_reveal_password=True,
            text_size=13,
            dense=True,
            filled=True,
            fill_color=ft.Colors.SURFACE,
            border=ft.OutlineInputBorder(
                side=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT), border_radius=9
            ),
            autocorrect=False,
            enable_suggestions=False,
            on_change=self.clear_token_error,
            on_submit=self.save_new_token,
        )
        self.token_error = ft.Text("", size=12, color=ft.Colors.ERROR, visible=False)
        self.login_button = ft.Button(
            "Log in",
            height=40,
            style=button_style(primary=True),
            on_click=self.save_new_token,
        )
        self.auth_view = soft_card(
            ft.Column(
                spacing=18,
                controls=[
                    self.step(
                        1,
                        "Copy the login script",
                        "You'll use it on Boosty in your browser.",
                        [self.copy_script_button, self.script_error],
                    ),
                    ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                    self.step(
                        2,
                        "Get your token on Boosty",
                        "Run the script while logged in to Boosty, then copy the token it returns.",
                        [self.instructions_button, self.instructions],
                    ),
                    ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                    self.step(
                        3,
                        "Connect your account",
                        None,
                        [
                            ft.Text(
                                "Boosty token", size=12, weight=ft.FontWeight.W_500
                            ),
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Container(self.token_text_field, expand=True),
                                    ft.IconButton(
                                        ft.Icons.CONTENT_PASTE,
                                        tooltip="Paste token",
                                        icon_size=19,
                                        on_click=self.paste_token,
                                    ),
                                ],
                            ),
                            self.token_error,
                            ft.Text(
                                "Use a token from the account you want to download from.",
                                size=11,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Container(
                                self.login_button, padding=ft.Padding.only(top=6)
                            ),
                        ],
                    ),
                ],
            ),
            padding=28,
        )
        self.auth_expires_info = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self.deauth_view = soft_card(
            ft.Column(
                spacing=18,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    soft_icon(ft.Icons.CHECK, 60),
                    ft.Text("Logged in", size=22, weight=ft.FontWeight.W_500),
                    ft.Text(
                        "Your Boosty account is connected.\nYou can download content included in your subscriptions.",
                        size=13,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True,
                        spacing=10,
                        controls=[
                            ft.Button(
                                "Back to home",
                                style=button_style(primary=True),
                                on_click=self.go_to_index,
                            ),
                            ft.OutlinedButton(
                                "Log out", style=button_style(), on_click=self.logout
                            ),
                        ],
                    ),
                    ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Token validity",
                                expand=True,
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            self.auth_expires_info,
                        ]
                    ),
                ],
            ),
            padding=30,
        )
        self.deauth_view.visible = False
        self.toolbar = components.AppBar(manager, on_auth_change=self.on_auth_change)
        self.controls = [
            page_shell(
                self.toolbar,
                ft.Column(
                    spacing=20,
                    controls=[
                        ft.Column(spacing=5, controls=[self.title, self.subtitle]),
                        self.auth_view,
                        self.deauth_view,
                    ],
                ),
                ft.Text(
                    "Access is limited to your Boosty subscriptions.",
                    expand=True,
                    size=11,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Icons.LOCK_OUTLINE,
                self.go_to_index,
                self.go_to_feedback,
                width=632,
            )
        ]

    @staticmethod
    def step(number, title, description, controls):
        badge = ft.Container(
            ft.Text(
                str(number),
                size=12,
                weight=ft.FontWeight.W_500,
                color=ft.Colors.PRIMARY,
            ),
            width=28,
            height=28,
            border_radius=9,
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            alignment=ft.Alignment.CENTER,
        )
        items = [ft.Text(title, size=14, weight=ft.FontWeight.W_500)]
        if description:
            items.append(
                ft.Text(description, size=12, color=ft.Colors.ON_SURFACE_VARIANT)
            )
        return ft.Row(
            [
                badge,
                ft.Column(
                    [ft.Column(items, spacing=6), ft.Column(controls, spacing=10)],
                    expand=True,
                    spacing=12,
                ),
            ],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def did_mount(self):
        self.refresh_task = asyncio.create_task(self.render_page())

    def will_unmount(self):
        for task in (self.refresh_task, self.copy_task):
            if task:
                task.cancel()

    def on_auth_change(self, logged_in):
        self.set_logged_in(logged_in)
        if self.refresh_task is not asyncio.current_task():
            if self.refresh_task:
                self.refresh_task.cancel()
            self.refresh_task = asyncio.create_task(self.render_page())

    def set_logged_in(self, logged_in):
        self.title.value = "Account" if logged_in else "Log in"
        self.subtitle.value = (
            "Manage your connection to Boosty."
            if logged_in
            else "Connect your Boosty account to access your subscriptions."
        )
        self.auth_view.visible = not logged_in
        self.deauth_view.visible = logged_in

    async def render_page(self):
        expires_at = await AuthorizationProvider.get_token_valid_to()
        now = datetime.datetime.now(datetime.UTC)
        logged_in = bool(expires_at and now < expires_at)
        self.set_logged_in(logged_in)
        if logged_in:
            delta = expires_at - now
            self.auth_expires_info.value = (
                f"{delta.days} days, {delta.seconds // 3600} hours"
                if delta.days
                else f"{delta.seconds // 3600} hours, {(delta.seconds // 60) % 60} minutes"
            )
        self.toolbar.set_auth_status(logged_in)
        self.update()

    async def go_to_index(self, e=None):
        await self.page.push_route("/")

    async def go_to_feedback(self, e=None):
        await self.page.push_route("/feedback-and-bugs")

    def toggle_instructions(self, e=None):
        self.instructions.visible = not self.instructions.visible
        self.instructions_button.content = (
            "Hide browser instructions"
            if self.instructions.visible
            else "Show browser instructions"
        )
        self.instructions_button.icon = (
            ft.Icons.KEYBOARD_ARROW_UP
            if self.instructions.visible
            else ft.Icons.KEYBOARD_ARROW_DOWN
        )
        self.update()

    def clear_token_error(self, e=None):
        self.token_error.visible = False
        self.update()

    async def paste_token(self, e=None):
        value = await ft.Clipboard().get()
        if value:
            self.token_text_field.value = value.strip()
            self.clear_token_error()

    async def copy_script(self, e=None):
        script_path = Path(__file__).resolve().parents[1] / "js/auth_getter_minify.js"
        try:
            async with aiofiles.open(script_path, mode="r", encoding="utf-8") as script:
                await ft.Clipboard().set(await script.read())
        except (OSError, RuntimeError):
            self.script_error.value = "Couldn't copy the script. Please try again."
            self.script_error.visible = True
            self.update()
            return
        self.script_error.visible = False
        self.copy_script_button.content = "Copied"
        self.copy_script_button.icon = ft.Icons.CHECK
        self.update()
        if self.copy_task:
            self.copy_task.cancel()
        self.copy_task = asyncio.create_task(self.reset_copy_button())

    async def reset_copy_button(self):
        await asyncio.sleep(2)
        self.copy_script_button.content = "Copy script"
        self.copy_script_button.icon = ft.Icons.CONTENT_COPY
        self.update()

    async def save_new_token(self, e=None):
        value = self.token_text_field.value.strip()
        token = AuthorizationProvider.validate_login(value) if value else None
        if not token:
            self.token_error.value = (
                "Paste your Boosty token to continue."
                if not value
                else "This token isn't valid. Check that you copied it completely."
            )
        elif token.expires_in <= datetime.datetime.now(datetime.UTC).timestamp():
            self.token_error.value = (
                "This token has expired. Get a new token on Boosty."
            )
        else:
            self.login_button.disabled = True
            self.update()
            try:
                await AuthorizationProvider.authorize(token)
                self.token_text_field.value = ""
                self.token_error.visible = False
                await self.render_page()
            finally:
                self.login_button.disabled = False
                self.update()
            return
        self.token_error.visible = True
        self.update()

    async def logout(self, e=None):
        preferences = ft.SharedPreferences()
        for key in ("ba-authorization", "ba-cookie", "ba-expires-in"):
            await preferences.remove(key)
        self.token_text_field.value = ""
        self.token_error.visible = False
        await self.render_page()
