from PySide6.QtWidgets import QApplication

THEMES = {
    "light": {
        "name": "Açık",
        "palette": {
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F5F7FA",
            "bg_tertiary": "#E8EBF0",
            "text_primary": "#1A1D29",
            "text_secondary": "#6B7280",
            "accent": "#2563EB",
            "accent_hover": "#1D4ED8",
            "border": "#D1D5DB",
            "scrollbar": "#CBD5E1",
        },
        "qss": """
            QMainWindow {
                background-color: #FFFFFF;
                color: #1A1D29;
            }

            QWidget {
                color: #1A1D29;
                font-family: "Segoe UI", "Helvetica", sans-serif;
                font-size: 10pt;
            }

            QLabel#section-title {
                font-size: 16pt;
                font-weight: bold;
                color: #1A1D29;
                padding: 0px 0px 4px 0px;
            }

            QLabel#subsection-title {
                font-size: 12pt;
                font-weight: 600;
                color: #374151;
                padding: 4px 0px 2px 0px;
            }

            QListWidget {
                background: #F5F7FA;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }

            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #E5E7EB;
            }

            QListWidget::item:last-child {
                border-bottom: none;
            }

            QListWidget::item:selected {
                background: linear-gradient(to right, #2563EB, #1D4ED8);
                color: white;
                border-radius: 6px;
            }

            QLineEdit, QTextEdit {
                background: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 8px 12px;
                color: #1A1D29;
                selection-background-color: #2563EB;
            }

            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #2563EB;
                padding: 7px 11px;
            }

            QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 10pt;
            }

            QPushButton:hover {
                background: #1D4ED8;
            }

            QPushButton:pressed {
                background: #1E40AF;
            }

            QPushButton:disabled {
                background: #D1D5DB;
                color: #9CA3AF;
            }

            QComboBox {
                background: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 8px 12px;
                color: #1A1D29;
            }

            QComboBox:focus {
                border: 2px solid #2563EB;
            }

            QComboBox::drop-down {
                border: none;
            }

            QComboBox::down-arrow {
                image: none;
                width: 0px;
            }

            QComboBox QAbstractItemView {
                background: #FFFFFF;
                selection-background-color: #2563EB;
                color: #1A1D29;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
            }

            QCheckBox {
                spacing: 8px;
                color: #1A1D29;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #D1D5DB;
                background: white;
            }

            QCheckBox::indicator:checked {
                background: #2563EB;
                border: 1px solid #2563EB;
                image: none;
            }

            QScrollBar:vertical {
                background: #F5F7FA;
                width: 8px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical {
                background: #BFC7D1;
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background: #A0ACB8;
            }

            QInputDialog QLabel {
                color: #1A1D29;
            }

            QInputDialog QLineEdit {
                padding: 8px 12px;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
            }

            QMessageBox QLabel {
                color: #1A1D29;
            }

            QMessageBox QPushButton {
                min-width: 50px;
            }
        """,
    },
    "dark": {
        "name": "Koyu",
        "palette": {
            "bg_primary": "#0F172A",
            "bg_secondary": "#1E293B",
            "bg_tertiary": "#334155",
            "text_primary": "#F1F5F9",
            "text_secondary": "#94A3B8",
            "accent": "#3B82F6",
            "accent_hover": "#2563EB",
            "border": "#475569",
            "scrollbar": "#64748B",
        },
        "qss": """
            QMainWindow {
                background-color: #0F172A;
                color: #F1F5F9;
            }

            QWidget {
                color: #F1F5F9;
                font-family: "Segoe UI", "Helvetica", sans-serif;
                font-size: 10pt;
            }

            QLabel#section-title {
                font-size: 16pt;
                font-weight: bold;
                color: #F1F5F9;
                padding: 0px 0px 4px 0px;
            }

            QLabel#subsection-title {
                font-size: 12pt;
                font-weight: 600;
                color: #CBD5E1;
                padding: 4px 0px 2px 0px;
            }

            QListWidget {
                background: #1E293B;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }

            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #334155;
                color: #F1F5F9;
            }

            QListWidget::item:last-child {
                border-bottom: none;
            }

            QListWidget::item:selected {
                background: linear-gradient(to right, #3B82F6, #2563EB);
                color: white;
                border-radius: 6px;
            }

            QLineEdit, QTextEdit {
                background: #1E293B;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 8px 12px;
                color: #F1F5F9;
                selection-background-color: #3B82F6;
            }

            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #3B82F6;
                padding: 7px 11px;
            }

            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 10pt;
            }

            QPushButton:hover {
                background: #2563EB;
            }

            QPushButton:pressed {
                background: #1D4ED8;
            }

            QPushButton:disabled {
                background: #475569;
                color: #94A3B8;
            }

            QComboBox {
                background: #1E293B;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 8px 12px;
                color: #F1F5F9;
            }

            QComboBox:focus {
                border: 2px solid #3B82F6;
            }

            QComboBox::drop-down {
                border: none;
            }

            QComboBox::down-arrow {
                image: none;
                width: 0px;
            }

            QComboBox QAbstractItemView {
                background: #1E293B;
                selection-background-color: #3B82F6;
                color: #F1F5F9;
                border: 1px solid #475569;
                border-radius: 6px;
            }

            QCheckBox {
                spacing: 8px;
                color: #F1F5F9;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #475569;
                background: #0F172A;
            }

            QCheckBox::indicator:checked {
                background: #3B82F6;
                border: 1px solid #3B82F6;
                image: none;
            }

            QScrollBar:vertical {
                background: #1E293B;
                width: 8px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical {
                background: #64748B;
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }

            QInputDialog QLabel {
                color: #F1F5F9;
            }

            QInputDialog QLineEdit {
                padding: 8px 12px;
                border: 1px solid #475569;
                border-radius: 6px;
                background: #1E293B;
                color: #F1F5F9;
            }

            QMessageBox QLabel {
                color: #F1F5F9;
            }

            QMessageBox QPushButton {
                min-width: 50px;
            }
        """,
    },
    "ocean": {
        "name": "Okyanus",
        "palette": {
            "bg_primary": "#F0F9FF",
            "bg_secondary": "#E0F2FE",
            "bg_tertiary": "#BAE6FD",
            "text_primary": "#0C2340",
            "text_secondary": "#0369A1",
            "accent": "#0284C7",
            "accent_hover": "#0369A1",
            "border": "#7DD3FC",
            "scrollbar": "#38BDF8",
        },
        "qss": """
            QMainWindow {
                background-color: #F0F9FF;
                color: #0C2340;
            }

            QWidget {
                color: #0C2340;
                font-family: "Segoe UI", "Helvetica", sans-serif;
                font-size: 10pt;
            }

            QLabel#section-title {
                font-size: 16pt;
                font-weight: bold;
                color: #0284C7;
                padding: 0px 0px 4px 0px;
            }

            QLabel#subsection-title {
                font-size: 12pt;
                font-weight: 600;
                color: #0369A1;
                padding: 4px 0px 2px 0px;
            }

            QListWidget {
                background: #E0F2FE;
                border: 1px solid #7DD3FC;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }

            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #BAE6FD;
            }

            QListWidget::item:last-child {
                border-bottom: none;
            }

            QListWidget::item:selected {
                background: linear-gradient(to right, #0284C7, #0369A1);
                color: white;
                border-radius: 6px;
            }

            QLineEdit, QTextEdit {
                background: #F0F9FF;
                border: 1px solid #7DD3FC;
                border-radius: 6px;
                padding: 8px 12px;
                color: #0C2340;
                selection-background-color: #0284C7;
            }

            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #0284C7;
                padding: 7px 11px;
            }

            QPushButton {
                background: #0284C7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 10pt;
            }

            QPushButton:hover {
                background: #0369A1;
            }

            QPushButton:pressed {
                background: #0C2340;
            }

            QPushButton:disabled {
                background: #BAE6FD;
                color: #0369A1;
            }

            QComboBox {
                background: #F0F9FF;
                border: 1px solid #7DD3FC;
                border-radius: 6px;
                padding: 8px 12px;
                color: #0C2340;
            }

            QComboBox:focus {
                border: 2px solid #0284C7;
            }

            QComboBox::drop-down {
                border: none;
            }

            QComboBox::down-arrow {
                image: none;
                width: 0px;
            }

            QComboBox QAbstractItemView {
                background: #F0F9FF;
                selection-background-color: #0284C7;
                color: #0C2340;
                border: 1px solid #7DD3FC;
                border-radius: 6px;
            }

            QCheckBox {
                spacing: 8px;
                color: #0C2340;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #7DD3FC;
                background: white;
            }

            QCheckBox::indicator:checked {
                background: #0284C7;
                border: 1px solid #0284C7;
                image: none;
            }

            QScrollBar:vertical {
                background: #E0F2FE;
                width: 8px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical {
                background: #38BDF8;
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background: #0EA5E9;
            }

            QInputDialog QLabel {
                color: #0C2340;
            }

            QInputDialog QLineEdit {
                padding: 8px 12px;
                border: 1px solid #7DD3FC;
                border-radius: 6px;
                background: #F0F9FF;
                color: #0C2340;
            }

            QMessageBox QLabel {
                color: #0C2340;
            }

            QMessageBox QPushButton {
                min-width: 50px;
            }
        """,
    },
}


def apply_theme(app: QApplication, theme_name: str):
    """Seçilen temayı uygular."""
    theme = THEMES.get(theme_name, THEMES["light"])
    app.setStyleSheet(theme["qss"])
