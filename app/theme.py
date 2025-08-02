from rich.theme import Theme

GRUVBOX_DARK_THEME = Theme(
    {
        # Gruvbox Dark palette – https://github.com/morhetz/gruvbox
        # -----------------------------------------------------------------
        # Core foreground / background colours
        "primary": "bold #ebdbb2",  # fg – light0
        "secondary": "#928374",  # gray – light4
        "accent": "#83a598",  # blue – bright_blue
        "text": "#d5c4a1",  # light3
        "comment": "#665c54",  # dark3
        # Semantic meanings ------------------------------------------------
        "danger": "bold #fb4934",  # bright_red
        "warning": "#fe8019",  # bright_orange
        "success": "#b8bb26",  # bright_green
        # Background -------------------------------------------------------
        "background": "#282828",  # dark0
    }
)
