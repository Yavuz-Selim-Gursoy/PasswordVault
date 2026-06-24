from PySide6.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# Giriş türleri için renkler
# Yeni tür eklemek için buraya satır eklemek yeterli.
# ---------------------------------------------------------------------------
TYPE_COLORS: dict[str, str] = {
    "password": "#EF5350",
    "username": "#42A5F5",
    "note": "#66BB6A",
    "email": "#AB47BC",
    "credit_card": "#FFA726",
    "address": "#29B6F6",
    "not_specified": "#78909C",
}

# ---------------------------------------------------------------------------
# Sıralama modları
# ---------------------------------------------------------------------------
SORT_OLDEST_FIRST = "oldest"
SORT_NEWEST_FIRST = "newest"
SORT_BY_BADGE = "badge"

SORT_OPTIONS: list[tuple[str, str]] = [
    (SORT_NEWEST_FIRST, "Yeniden Eskiye"),
    (SORT_OLDEST_FIRST, "Eskiden Yeniye"),
    (SORT_BY_BADGE, "Türe Göre (A-Z)"),
]

# ---------------------------------------------------------------------------
# Ölçek (asset/arayüz büyütme)
# ---------------------------------------------------------------------------
SCALE_OPTIONS: list[int] = [50, 100, 150, 200]
DEFAULT_SCALE = 100
CURRENT_SCALE = DEFAULT_SCALE


def set_current_scale(scale: int) -> None:
    """Aktif ölçeği günceller. Geçersiz bir değer gelirse varsayılana döner."""
    global CURRENT_SCALE
    CURRENT_SCALE = scale if scale in SCALE_OPTIONS else DEFAULT_SCALE


def scale_value(base: float, scale: int | None = None, minimum: int = 1) -> int:
    """Bir temel boyutu (px/pt) aktif (veya verilen) ölçeğe göre ölçekler."""
    s = scale if scale is not None else CURRENT_SCALE
    return max(minimum, round(base * s / 100))


# ---------------------------------------------------------------------------
# Temalar
# Yeni tema eklemek için THEMES sözlüğüne yeni bir blok eklemek yeterli.
# ---------------------------------------------------------------------------
def _build_qss(c: dict, scale: int = DEFAULT_SCALE) -> str:
    sv = lambda px: scale_value(px, scale)  # noqa: E731
    fs = lambda pt: scale_value(pt, scale, minimum=6)  # noqa: E731

    return f"""
        QMainWindow {{ background-color: {c["bg_primary"]}; color: {c["text_primary"]}; }}

        QWidget {{
            color: {c["text_primary"]};
            font-family: "Segoe UI", "Helvetica", sans-serif;
            font-size: {fs(10)}pt;
        }}

        QDialog {{ background-color: {c["bg_secondary"]}; }}
        QDialog QLabel    {{ color: {c["text_primary"]}; }}
        QDialog QLineEdit {{ background: {c["bg_primary"]}; color: {c["text_primary"]}; }}
        QDialog QComboBox {{ background: {c["bg_primary"]}; color: {c["text_primary"]}; }}
        QDialog QCheckBox {{ color: {c["text_primary"]}; }}

        QLabel#section-title {{
            font-size: {fs(16)}pt; font-weight: bold;
            color: {c["title"]}; padding: 0px 0px {sv(4)}px 0px;
        }}
        QLabel#subsection-title {{
            font-size: {fs(12)}pt; font-weight: 600;
            color: {c["text_secondary"]}; padding: {sv(4)}px 0px {sv(2)}px 0px;
        }}

        QListWidget {{
            background: {c["bg_secondary"]};
            border: 3px solid {c["border"]};
            border-radius: {sv(8)}px; padding: {sv(16)}px; outline: none;
        }}
        QListWidget::item {{
            padding: 0px; border-bottom: 1px solid {c["bg_tertiary"]};
            color: {c["text_primary"]};
        }}
        QListWidget::item:last-child {{ border-bottom: none; }}
        QListWidget::item:hover {{
            background: {c["item_hover"]}; border-radius: {sv(6)}px;
        }}
        QListWidget::item:selected {{
            background: {c["accent"]}; color: white; border-radius: {sv(6)}px;
        }}

        QWidget#entry-detail {{
            background: {c["detail_bg"]};
            border-left: 3px solid {c["detail_border"]};
            border-radius: {sv(4)}px;
        }}
        QLabel#detail-field-title {{ color: {c["detail_title"]}; }}

        QWidget#entry-row {{
            background-color: {c["entry_bg"]};
            border: 1px solid {c["entry_border"]};
            border-radius: 8px; margin: 2px 6px;
        }}
        QWidget#entry-row:hover {{ background-color: {c["entry_hover"]}; }}

        QWidget#vault-row {{
            background-color: transparent;
            border-left: 3px solid transparent;
            border-radius: 6px; margin: 1px 4px;
        }}
        QWidget#vault-row:hover {{ background-color: {c["vault_hover"]}; }}
        QWidget#vault-row[selected="true"] {{
            background-color: {c["vault_selected_bg"]};
            border-left: 3px solid {c["accent"]};
        }}

        QLineEdit, QTextEdit {{
            background: {c["bg_primary"]}; border: 1px solid {c["border"]};
            border-radius: {sv(6)}px; padding: {sv(8)}px {sv(12)}px;
            color: {c["text_primary"]}; selection-background-color: {c["accent"]};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border: 2px solid {c["accent"]}; padding: {sv(7)}px {sv(11)}px;
        }}

        QPushButton {{
            background: {c["accent"]}; color: white;
            border: none; border-radius: {sv(6)}px;
            padding: {sv(8)}px {sv(16)}px; font-weight: 600; font-size: {fs(10)}pt;
        }}
        QPushButton:hover   {{ background: {c["accent_hover"]}; }}
        QPushButton:pressed {{ background: {c["accent_pressed"]}; }}
        QPushButton:disabled {{ background: {c["disabled_bg"]}; color: {c["disabled_text"]}; }}

        QPushButton#settings-btn {{
            background: transparent; border: none;
            font-size: {fs(14)}pt; padding: 0px; color: {c["text_secondary"]};
        }}
        QPushButton#settings-btn:hover {{ color: {c["accent"]}; }}

        QMenuBar {{
            background-color: {c["bg_primary"]};
            color: {c["text_primary"]};
            border-bottom: 1px solid {c["border"]};
        }}
        QMenuBar::item {{
            padding: {sv(4)}px {sv(10)}px;
            border-radius: {sv(4)}px;
            color: {c["text_primary"]};
            background: transparent;
        }}
        QMenuBar::item:selected {{ background: {c["accent"]}; color: white; }}
        QMenuBar::item:pressed  {{ background: {c["accent_pressed"]}; color: white; }}

        QMenu {{
            background: {c["bg_secondary"]};
            border: 1px solid {c["border"]};
            border-radius: {sv(6)}px; padding: {sv(4)}px;
        }}
        QMenu::item {{
            padding: {sv(6)}px {sv(20)}px; border-radius: {sv(4)}px; color: {c["text_primary"]};
        }}
        QMenu::item:selected {{ background: {c["accent"]}; color: white; }}

        QComboBox {{
            background: {c["bg_primary"]}; border: 1px solid {c["border"]};
            border-radius: {sv(6)}px; padding: {sv(8)}px {sv(12)}px; color: {c["text_primary"]};
        }}
        QComboBox:focus {{ border: 2px solid {c["accent"]}; }}
        QComboBox::drop-down {{ border: none; }}
        QComboBox::down-arrow {{ image: none; width: 0px; }}
        QComboBox QAbstractItemView {{
            background: {c["bg_primary"]}; color: {c["text_primary"]};
            selection-background-color: {c["accent"]};
            border: 1px solid {c["border"]}; border-radius: {sv(6)}px;
        }}

        QSpinBox {{
            background: {c["bg_primary"]}; border: 1px solid {c["border"]};
            border-radius: {sv(6)}px; padding: {sv(6)}px {sv(10)}px;
            color: {c["text_primary"]}; selection-background-color: {c["accent"]};
        }}
        QSpinBox:focus {{ border: 2px solid {c["accent"]}; }}
        QSpinBox::up-button, QSpinBox::down-button {{
            background: transparent; border: none; width: {sv(18)}px;
        }}

        QFrame#section-separator {{
            border: none;
            border-top: 1px solid {c["border"]};
            max-height: 1px;
            margin: {sv(2)}px 0px;
        }}

        QCheckBox {{ spacing: {sv(8)}px; color: {c["text_primary"]}; }}
        QCheckBox::indicator {{
            width: {sv(18)}px; height: {sv(18)}px;
            border-radius: {sv(3)}px; border: 1px solid {c["border"]};
            background: {c["bg_primary"]};
        }}
        QCheckBox::indicator:checked {{
            background: {c["accent"]}; border: 1px solid {c["accent"]}; image: none;
        }}

        QScrollBar:vertical {{
            background: {c["bg_secondary"]}; width: {sv(8)}px; border-radius: {sv(4)}px;
        }}
        QScrollBar::handle:vertical {{
            background: {c["scrollbar"]}; border-radius: {sv(4)}px; min-height: {sv(20)}px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {c["scrollbar_hover"]}; }}

        QInputDialog {{ background: {c["bg_secondary"]}; }}
        QInputDialog QLabel    {{ color: {c["text_primary"]}; }}
        QInputDialog QLineEdit {{
            padding: {sv(8)}px {sv(12)}px; border: 1px solid {c["border"]};
            border-radius: {sv(6)}px; background: {c["bg_primary"]}; color: {c["text_primary"]};
        }}

        QMessageBox {{ background: {c["bg_secondary"]}; }}
        QMessageBox QLabel      {{ color: {c["text_primary"]}; }}
        QMessageBox QPushButton {{ min-width: {sv(50)}px; }}
    """


THEMES: dict[str, dict] = {
    "light": {
        "name": "Açık",
        "colors": {
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F5F7FA",
            "bg_tertiary": "#E8EBF0",
            "text_primary": "#1A1D29",
            "text_secondary": "#6B7280",
            "title": "#1A1D29",
            "accent": "#2563EB",
            "accent_hover": "#1D4ED8",
            "accent_pressed": "#1E40AF",
            "border": "#D1D5DB",
            "scrollbar": "#BFC7D1",
            "scrollbar_hover": "#A0ACB8",
            "disabled_bg": "#D1D5DB",
            "disabled_text": "#9CA3AF",
            "item_hover": "rgba(240,244,248,150)",
            "detail_bg": "rgba(37,99,235,18)",
            "detail_border": "rgba(37,99,235,130)",
            "detail_title": "#1D4ED8",
            "entry_bg": "#E8EBF0",
            "entry_border": "rgba(37,99,235,120)",
            "entry_hover": "#DBE1E9",
            "vault_hover": "rgba(37,99,235,18)",
            "vault_selected_bg": "rgba(37,99,235,30)",
        },
    },
    "dark": {
        "name": "Koyu",
        "colors": {
            "bg_primary": "#0F172A",
            "bg_secondary": "#1E293B",
            "bg_tertiary": "#334155",
            "text_primary": "#F1F5F9",
            "text_secondary": "#94A3B8",
            "title": "#F1F5F9",
            "accent": "#3B82F6",
            "accent_hover": "#2563EB",
            "accent_pressed": "#1D4ED8",
            "border": "#475569",
            "scrollbar": "#64748B",
            "scrollbar_hover": "#94A3B8",
            "disabled_bg": "#475569",
            "disabled_text": "#94A3B8",
            "item_hover": "rgba(51,65,85,150)",
            "detail_bg": "rgba(59,130,246,22)",
            "detail_border": "rgba(59,130,246,140)",
            "detail_title": "#60A5FA",
            "entry_bg": "#334155",
            "entry_border": "rgba(59,130,246,130)",
            "entry_hover": "#2A3647",
            "vault_hover": "rgba(59,130,246,25)",
            "vault_selected_bg": "rgba(59,130,246,35)",
        },
    },
    "ocean": {
        "name": "Okyanus",
        "colors": {
            "bg_primary": "#F0F9FF",
            "bg_secondary": "#E0F2FE",
            "bg_tertiary": "#BAE6FD",
            "text_primary": "#0C2340",
            "text_secondary": "#0369A1",
            "title": "#0284C7",
            "accent": "#0284C7",
            "accent_hover": "#0369A1",
            "accent_pressed": "#0C2340",
            "border": "#7DD3FC",
            "scrollbar": "#38BDF8",
            "scrollbar_hover": "#0EA5E9",
            "disabled_bg": "#BAE6FD",
            "disabled_text": "#0369A1",
            "item_hover": "rgba(202,240,248,150)",
            "detail_bg": "rgba(2,132,199,20)",
            "detail_border": "rgba(2,132,199,130)",
            "detail_title": "#0369A1",
            "entry_bg": "#BAE6FD",
            "entry_border": "rgba(2,132,199,120)",
            "entry_hover": "#9DD9F9",
            "vault_hover": "rgba(2,132,199,25)",
            "vault_selected_bg": "rgba(2,132,199,35)",
        },
    },
    "gece": {
        "name": "Gece",
        "colors": {
            "bg_primary": "#111119",
            "bg_secondary": "#1A1A28",
            "bg_tertiary": "#1E1E30",
            "text_primary": "#D8DCE8",
            "text_secondary": "#8A90A8",
            "title": "#9B99D6",
            "accent": "#6366F1",
            "accent_hover": "#5558D4",
            "accent_pressed": "#4547B8",
            "border": "#3A3A7A",
            "scrollbar": "#454580",
            "scrollbar_hover": "#5558D4",
            "disabled_bg": "#3A3A7A",
            "disabled_text": "#8A90A8",
            "item_hover": "rgba(99,102,241,20)",
            "detail_bg": "rgba(99,102,241,22)",
            "detail_border": "rgba(99,102,241,140)",
            "detail_title": "#9B99D6",
            "entry_bg": "#1C1C2C",
            "entry_border": "rgba(99,102,241,120)",
            "entry_hover": "#161622",
            "vault_hover": "rgba(99,102,241,20)",
            "vault_selected_bg": "rgba(99,102,241,30)",
        },
    },
    "orman": {
        "name": "Orman",
        "colors": {
            "bg_primary": "#F5F8F5",
            "bg_secondary": "#E4EEE6",
            "bg_tertiary": "#C8DDD0",
            "text_primary": "#2A4A38",
            "text_secondary": "#3D6650",
            "title": "#4A7C59",
            "accent": "#4A7C59",
            "accent_hover": "#3D6650",
            "accent_pressed": "#2A4A38",
            "border": "#9EC8B0",
            "scrollbar": "#7AB895",
            "scrollbar_hover": "#5A9E78",
            "disabled_bg": "#C8DDD0",
            "disabled_text": "#3D6650",
            "item_hover": "rgba(74,124,89,18)",
            "detail_bg": "rgba(74,124,89,20)",
            "detail_border": "rgba(74,124,89,130)",
            "detail_title": "#3D6650",
            "entry_bg": "#C8DDD0",
            "entry_border": "rgba(74,124,89,120)",
            "entry_hover": "#B8D0C0",
            "vault_hover": "rgba(74,124,89,25)",
            "vault_selected_bg": "rgba(74,124,89,35)",
        },
    },
    "gul": {
        "name": "Gül",
        "colors": {
            "bg_primary": "#FBF5F6",
            "bg_secondary": "#F5E8EA",
            "bg_tertiary": "#EDD5D8",
            "text_primary": "#6B3040",
            "text_secondary": "#7A3A4A",
            "title": "#B05570",
            "accent": "#B05570",
            "accent_hover": "#964460",
            "accent_pressed": "#7A3040",
            "border": "#DBAAB5",
            "scrollbar": "#C89099",
            "scrollbar_hover": "#B07080",
            "disabled_bg": "#EDD5D8",
            "disabled_text": "#7A3A4A",
            "item_hover": "rgba(176,85,112,18)",
            "detail_bg": "rgba(176,85,112,18)",
            "detail_border": "rgba(176,85,112,130)",
            "detail_title": "#964460",
            "entry_bg": "#EDD5D8",
            "entry_border": "rgba(176,85,112,120)",
            "entry_hover": "#DBAAB5",
            "vault_hover": "rgba(176,85,112,25)",
            "vault_selected_bg": "rgba(176,85,112,35)",
        },
    },
}

# QSS her tema + ölçek kombinasyonu için önceden üretilir
for _key, _theme in THEMES.items():
    _theme["qss_by_scale"] = {
        _scale: _build_qss(_theme["colors"], _scale) for _scale in SCALE_OPTIONS
    }
    _theme["qss"] = _theme["qss_by_scale"][DEFAULT_SCALE]


def apply_theme(app: QApplication, theme_name: str, scale: int | None = None) -> None:
    """Seçilen temayı (ve ölçeği) uygular."""
    theme = THEMES.get(theme_name, THEMES["light"])
    s = scale if scale in SCALE_OPTIONS else CURRENT_SCALE
    qss = theme["qss_by_scale"].get(s, theme["qss"])
    app.setStyleSheet(qss)
