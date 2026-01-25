import flet as ft


LIGHT_COLORS = {
    "background": "#f6f6f6",
    "surface": "#ffffff",
    "text_primary": "#202829",
    "text_secondary": "#5c6b6c",
    "primary": "#db7943",
    "primary_variant": "#ffc2af",
    "secondary": "#5c6b6c",
    "error": "#e53935",
    "success": "#4caf50",
}

DARK_COLORS = {
    "background": "#121212",
    "surface": "#1e1e1e",
    "text_primary": "#e0e0e0",
    "text_secondary": "#a0a0a0",
    "primary": "#db7943",
    "primary_variant": "#402a18",
    "secondary": "#8e9e9f",
    "error": "#ff6b6b",
    "success": "#81c784",
}


LIGHT_THEME = ft.Theme(
    color_scheme=ft.ColorScheme(
        primary=LIGHT_COLORS["primary"],
        primary_container=LIGHT_COLORS["primary_variant"],
        secondary=LIGHT_COLORS["secondary"],
        surface=LIGHT_COLORS["surface"],
        on_surface=LIGHT_COLORS["text_primary"],
        on_primary=LIGHT_COLORS["surface"],
        on_secondary=LIGHT_COLORS["surface"],
        error=LIGHT_COLORS["error"],
    ),
    text_theme=ft.TextTheme(
        body_large=ft.TextStyle(color=LIGHT_COLORS["text_primary"]),
        body_medium=ft.TextStyle(color=LIGHT_COLORS["text_primary"]),
        body_small=ft.TextStyle(color=LIGHT_COLORS["text_secondary"]),
        title_large=ft.TextStyle(
            color=LIGHT_COLORS["text_primary"],
            weight=ft.FontWeight.BOLD
        ),
        title_medium=ft.TextStyle(
            color=LIGHT_COLORS["text_primary"],
            weight=ft.FontWeight.W_600
        ),
        label_large=ft.TextStyle(color=LIGHT_COLORS["text_secondary"]),
    ),
)

DARK_THEME = ft.Theme(
    color_scheme=ft.ColorScheme(
        primary=DARK_COLORS["primary"],
        primary_container=DARK_COLORS["primary_variant"],
        secondary=DARK_COLORS["secondary"],
        surface=DARK_COLORS["surface"],
        on_surface=DARK_COLORS["text_primary"],
        on_primary=DARK_COLORS["surface"],
        on_secondary=DARK_COLORS["surface"],
        error=DARK_COLORS["error"],
    ),
    text_theme=ft.TextTheme(
        body_large=ft.TextStyle(color=DARK_COLORS["text_primary"]),
        body_medium=ft.TextStyle(color=DARK_COLORS["text_primary"]),
        body_small=ft.TextStyle(color=DARK_COLORS["text_secondary"]),
        title_large=ft.TextStyle(
            color=DARK_COLORS["text_primary"],
            weight=ft.FontWeight.BOLD
        ),
        title_medium=ft.TextStyle(
            color=DARK_COLORS["text_primary"],
            weight=ft.FontWeight.W_600
        ),
        label_large=ft.TextStyle(color=DARK_COLORS["text_secondary"]),
    ),
)