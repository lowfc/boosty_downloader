import flet as ft

from localization import Localizer
from themes import HOME_DARK_THEME, HOME_LIGHT_THEME


def button_style(primary=False):
    return ft.ButtonStyle(
        color=(
            {
                ft.ControlState.DEFAULT: "#ffffff",
                ft.ControlState.DISABLED: ft.Colors.ON_SURFACE_VARIANT,
            }
            if primary
            else ft.Colors.ON_SURFACE
        ),
        bgcolor=(
            {
                ft.ControlState.DEFAULT: "#bb5727",
                ft.ControlState.DISABLED: ft.Colors.SURFACE_CONTAINER_HIGHEST,
            }
            if primary
            else ft.Colors.SURFACE_CONTAINER_LOWEST
        ),
        side=ft.BorderSide(0 if primary else 1, ft.Colors.OUTLINE_VARIANT),
        shape=ft.RoundedRectangleBorder(radius=9),
        elevation=0,
        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_500),
    )


def soft_card(content, padding=26):
    return ft.Container(
        content=content,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=18,
        padding=padding,
    )


def soft_icon(icon, size=38):
    return ft.Container(
        ft.Icon(icon, size=size * 0.48, color=ft.Colors.PRIMARY),
        width=size,
        height=size,
        border_radius=size * 0.28,
        bgcolor=ft.Colors.PRIMARY_CONTAINER,
        alignment=ft.Alignment.CENTER,
    )


def page_shell(
    toolbar,
    body,
    footer_note,
    footer_icon,
    on_feedback,
    width,
    footer_action_label="Feedback",
    localizer=None,
):
    tr = (localizer or Localizer()).t
    return ft.Container(
        expand=True,
        bgcolor=ft.Colors.SURFACE,
        theme=HOME_LIGHT_THEME,
        dark_theme=HOME_DARK_THEME,
        content=ft.Column(
            spacing=0,
            controls=[
                toolbar,
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.TOP_CENTER,
                    padding=ft.Padding.symmetric(horizontal=32, vertical=12),
                    content=ft.Column(
                        width=width,
                        spacing=10,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[body],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=24, vertical=10),
                    border=ft.Border.only(
                        top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
                    ),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(
                                footer_icon, size=14, color=ft.Colors.ON_SURFACE_VARIANT
                            ),
                            footer_note,
                            ft.TextButton(
                                tr(footer_action_label),
                                on_click=on_feedback,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                    text_style=ft.TextStyle(size=11),
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
