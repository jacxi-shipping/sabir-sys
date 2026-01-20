"""UI helper utilities: centralized theming and common widget factories."""
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtCore import Qt

from egg_farm_system.ui.themes import ThemeManager
from egg_farm_system import config


def apply_theme(app: QApplication, theme_name: Optional[str] = None) -> None:
    """Apply consolidated stylesheet: project `styles.qss` plus ThemeManager stylesheet.

    If `theme_name` is not provided, `config.DEFAULT_THEME` is used.
    """
    theme = theme_name or getattr(config, 'DEFAULT_THEME', None)

    # Load existing styles.qss (if available) and then append theme-specific rules.
    try:
        base = Path(__file__).parent.parent
        qss_path = base / 'styles.qss'
        qss = ''
        if qss_path.exists():
            qss = qss_path.read_text(encoding='utf-8') + '\n'

        # Append ThemeManager stylesheet if theme provided
        if theme:
            qss += ThemeManager.get_stylesheet(theme)

        if qss:
            app.setStyleSheet(qss)
    except Exception:
        # Fail silently; caller may have own logging
        return


def create_button(text: str, style: str = 'primary') -> QPushButton:
    """Create a QPushButton with standardized properties and a CSS class.

    style values: 'primary', 'danger', 'success', 'ghost'
    """
    btn = QPushButton(text)
    btn.setProperty('class', style)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setMinimumHeight(32)
    return btn
