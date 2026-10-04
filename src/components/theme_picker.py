from collections.abc import Callable
from enum import Enum

import flet as ft

from localization import Localizer


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


theme_icons = {
    ThemeMode.LIGHT: ft.Icons.LIGHT_MODE,
    ThemeMode.DARK: ft.Icons.DARK_MODE,
    ThemeMode.SYSTEM: ft.Icons.DESKTOP_WINDOWS_OUTLINED,
}
theme_names = {
    ThemeMode.LIGHT: "Light",
    ThemeMode.DARK: "Dark",
    ThemeMode.SYSTEM: "System",
}


@ft.control
class ThemePicker(ft.Column):
    """Choose a draft theme; the settings form owns preview and persistence."""

    def __init__(
        self, on_theme_change: Callable[[str], None] | None = None, localizer=None
    ):
        super().__init__()
        self.localizer = localizer or Localizer()
        self.tr = self.localizer.t
        self.value = "system"
        self.on_theme_change = on_theme_change
        self.spacing = 9
        self.buttons = {}
        for mode in ThemeMode:
            self.buttons[mode.value] = ft.OutlinedButton(
                self.tr(theme_names[mode]),
                icon=theme_icons[mode],
                height=44,
                expand=True,
                on_click=lambda e, selected=mode.value: self.select(selected),
            )
        self.help_text = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self.controls = [
            ft.Row(list(self.buttons.values()), spacing=10),
            self.help_text,
        ]
        self.set_value("system")

    def set_value(self, value):
        self.value = value if value in self.buttons else "system"
        for key, button in self.buttons.items():
            selected = key == self.value
            button.style = ft.ButtonStyle(
                color=ft.Colors.PRIMARY if selected else ft.Colors.ON_SURFACE_VARIANT,
                bgcolor=(
                    ft.Colors.PRIMARY_CONTAINER
                    if selected
                    else ft.Colors.SURFACE_CONTAINER_LOWEST
                ),
                side=ft.BorderSide(
                    1, ft.Colors.PRIMARY if selected else ft.Colors.OUTLINE_VARIANT
                ),
                shape=ft.RoundedRectangleBorder(radius=9),
                padding=ft.Padding.symmetric(horizontal=10, vertical=12),
                text_style=ft.TextStyle(
                    size=13,
                    weight=ft.FontWeight.W_500 if selected else ft.FontWeight.W_400,
                ),
            )
        self.help_text.value = (
            self.tr("Follows your system appearance.")
            if self.value == "system"
            else self.tr(
                "{theme} appearance selected.",
                theme=(
                    self.tr(theme_names[ThemeMode(self.value)]).lower()
                    if self.localizer.language == "ru"
                    else theme_names[ThemeMode(self.value)]
                ),
            )
        )

    def select(self, value):
        self.set_value(value)
        if self.on_theme_change:
            self.on_theme_change(self.value)
        else:
            self.update()
