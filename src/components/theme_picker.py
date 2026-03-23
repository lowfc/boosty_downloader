import asyncio
from enum import Enum

import flet as ft


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


theme_icons = {
    ThemeMode.LIGHT: ft.Icons.LIGHT_MODE,
    ThemeMode.DARK: ft.Icons.DARK_MODE,
    ThemeMode.SYSTEM: ft.Icons.BRIGHTNESS_AUTO,
}

theme_names = {
    ThemeMode.LIGHT: "Light",
    ThemeMode.DARK: "Dark",
    ThemeMode.SYSTEM: "System",
}


@ft.control
class ThemePicker(ft.Dropdown):
    def __init__(self):
        super().__init__()
        self.height = 50
        self.width = 700
        self.border_color = ft.Colors.TRANSPARENT
        self.filled = True
        self.fill_color = ft.Colors.SURFACE_CONTAINER
        self.text_size = 14
        self.content_padding = ft.padding.symmetric(horizontal=16, vertical=12)
        self.prefix_icon = theme_icons[ThemeMode.SYSTEM]
        self.value = ThemeMode.SYSTEM.value
        self.on_select = lambda e: asyncio.create_task(
            self.apply_theme(ThemeMode(e.data))
        )
        asyncio.create_task(self.actualize_self())

        self.options = [
            ft.dropdown.Option(
                key=ThemeMode.LIGHT.value,
                text=theme_names[ThemeMode.LIGHT],
                content=ft.Row(
                    [
                        ft.Icon(theme_icons[ThemeMode.LIGHT], size=20),
                        ft.Text(theme_names[ThemeMode.LIGHT]),
                    ]
                ),
            ),
            ft.dropdown.Option(
                key=ThemeMode.DARK.value,
                text=theme_names[ThemeMode.DARK],
                content=ft.Row(
                    [
                        ft.Icon(theme_icons[ThemeMode.DARK], size=20),
                        ft.Text(theme_names[ThemeMode.DARK]),
                    ]
                ),
            ),
            ft.dropdown.Option(
                key=ThemeMode.SYSTEM.value,
                text=theme_names[ThemeMode.SYSTEM],
                content=ft.Row(
                    [
                        ft.Icon(theme_icons[ThemeMode.SYSTEM], size=20),
                        ft.Text(theme_names[ThemeMode.SYSTEM]),
                    ]
                ),
            ),
        ]

    async def actualize_self(self):
        raw_mode = await ft.SharedPreferences().get("current-app-theme") or "system"
        mode = ThemeMode(raw_mode)
        if mode == ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        elif mode == ThemeMode.DARK:
            self.page.theme_mode = ft.ThemeMode.DARK
        else:  # SYSTEM
            self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.prefix_icon = theme_icons[mode]
        self.value = mode.value
        self.page.update()

    async def apply_theme(self, mode: ThemeMode):
        await ft.SharedPreferences().set("current-app-theme", mode.value)
        await self.actualize_self()
