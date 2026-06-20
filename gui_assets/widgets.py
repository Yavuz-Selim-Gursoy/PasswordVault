import base64
import hashlib
import os
from typing import Optional

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.entry import Entry
from src.vault import PasswordVault

# Türler için renkler
TYPE_COLORS = {
    "password": "#EF5350",
    "username": "#42A5F5",
    "note": "#66BB6A",
    "email": "#AB47BC",
    "credit_card": "#FFA726",
    "address": "#29B6F6",
    "not_specified": "#78909C",
}

# Sıralama modları
SORT_OLDEST_FIRST = "oldest"
SORT_NEWEST_FIRST = "newest"
SORT_BY_BADGE = "badge"

SORT_OPTIONS = [
    (SORT_NEWEST_FIRST, "Yeniden Eskiye"),
    (SORT_OLDEST_FIRST, "Eskiden Yeniye"),
    (SORT_BY_BADGE, "Türe Göre (A-Z)"),
]


def derive_vault_filename(
    vault_name: str, password: bytes, secretive: bool = True
) -> str:
    """Kasa dosya adını türetir."""
    if secretive:
        h = hashlib.blake2b(
            vault_name.encode("utf-8"), key=password, digest_size=16
        ).digest()
        return base64.urlsafe_b64encode(h).decode("ascii") + ".pvlt"

    else:
        return vault_name + ".pvlt"


def get_color_for_type(data_type: str) -> QColor:
    """Türe göre renk döndürür."""
    return QColor(TYPE_COLORS.get(data_type, "#78909C"))


def copy_to_clipboard(text: str):
    """Verilen metni panoya kopyalar."""
    QGuiApplication.clipboard().setText(text or "")


class EntryTypeBadge(QLabel):
    """Giriş türü etiketi."""

    def __init__(self, data_type: str, parent=None):
        super().__init__(data_type, parent)
        color = get_color_for_type(data_type)
        self.setStyleSheet(f"""
            background-color: {color.name()};
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.3px;
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(24)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.adjustSize()


class CopyButton(QPushButton):
    """Küçük, sade bir 'kopyala' butonu. Tıklayınca değeri panoya kopyalar
    ve kısa süreliğine geri bildirim gösterir."""

    def __init__(self, value: str, parent=None):
        super().__init__("Kopyala", parent)
        self.value = value
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(24)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #2563EB;
                border: 1px solid #2563EB;
                border-radius: 10px;
                padding: 2px 10px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(37, 99, 235, 30);
            }
            QPushButton:pressed {
                background: rgba(37, 99, 235, 60);
            }
        """)
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        copy_to_clipboard(self.value)
        original = "Kopyala"
        self.setText("Kopyalandı")
        self.setEnabled(False)
        QTimer.singleShot(1000, lambda: (self.setText(original), self.setEnabled(True)))


class EntryRowWidget(QWidget):
    """Tek bir giriş satırı. Tıklanınca ek notu açılır/kapanır."""

    def __init__(self, entry, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.expanded = False
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        header = QWidget()
        header.setMinimumHeight(44)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 6, 12, 6)
        h_layout.setSpacing(10)

        # İsim
        name_label = QLabel(self.entry.name)
        name_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        name_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Değer (kırpılmış / elided metin)
        value_label = QLabel()
        value_label.setStyleSheet("color: #90A4AE; font-size: 9pt;")
        value_label.setMaximumWidth(150)
        value_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        fm = QFontMetrics(value_label.font())
        elided = fm.elidedText(self.entry.value or "", Qt.ElideRight, 150)
        value_label.setText(elided)
        if self.entry.value:
            value_label.setToolTip(self.entry.value)

        # Badge
        badge = EntryTypeBadge(self.entry.data_type)

        # Kopyala butonu
        copy_btn = CopyButton(self.entry.value or "")

        h_layout.addWidget(name_label, 0, Qt.AlignVCenter)
        h_layout.addWidget(value_label, 0, Qt.AlignVCenter)
        h_layout.addStretch()
        h_layout.addWidget(badge, 0, Qt.AlignVCenter)
        h_layout.addWidget(copy_btn, 0, Qt.AlignVCenter)

        self.main_layout.addWidget(header)

        note_text = self.entry.additional_note or "Bu giriş için not eklenmemiş."
        self.note_label = QLabel(note_text)
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet("""
            color: #607D8B;
            font-size: 9pt;
            font-style: italic;
            padding: 0px 16px 12px 16px;
        """)
        self.note_label.setVisible(False)
        self.main_layout.addWidget(self.note_label)

    def toggle(self):
        """Notu aç/kapat."""
        self.expanded = not self.expanded
        self.note_label.setVisible(self.expanded)


class VaultListWidget(QWidget):
    """Sol panel: kasa listesi ve hızlı açma formu."""

    vault_selected = Signal(str)
    vault_open_requested = Signal(str, str, bool)

    def __init__(self, vaults_dir: str, parent=None):
        super().__init__(parent)
        self.vaults_dir = vaults_dir
        self._init_ui()
        self.refresh_list()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Başlık
        title = QLabel("Kasalar")
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        title.setFont(title_font)
        title.setObjectName("section-title")
        layout.addWidget(title)

        # Kasa listesi
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.currentTextChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.new_btn = QPushButton("Yeni Kasa")
        self.new_btn.clicked.connect(self._create_new_vault)

        self.open_btn = QPushButton("Seçileni Aç")
        self.open_btn.clicked.connect(self._open_selected_vault)

        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.open_btn)
        layout.addLayout(btn_layout)

        # Hızlı Açma Bölümü
        quick_title = QLabel("Hızlı Aç")
        quick_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        quick_title.setObjectName("subsection-title")
        layout.addWidget(quick_title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Kasa adı (şifreli değilse)")
        self.name_input.setMinimumHeight(36)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Master parola")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(36)

        self.secretive_check = QCheckBox("Kasa adı şifreli mi?")
        self.secretive_check.setStyleSheet("spacing: 8px; padding: 4px;")

        self.quick_open_btn = QPushButton("Aç")
        self.quick_open_btn.clicked.connect(self._quick_open)
        self.quick_open_btn.setMinimumHeight(36)

        layout.addWidget(self.name_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.secretive_check)
        layout.addWidget(self.quick_open_btn)

        layout.addStretch()

    def refresh_list(self):
        """Vault dosyalarını listeler."""
        self.list_widget.clear()
        if not os.path.exists(self.vaults_dir):
            os.makedirs(self.vaults_dir)

        for f in os.listdir(self.vaults_dir):
            if f.endswith(".pvlt"):
                self.list_widget.addItem(f)

    def _on_selection_changed(self, current_text: str):
        pass

    def _open_selected_vault(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "Uyarı", "Lütfen listeden bir kasa seçin.")
            return

        filename = item.text()
        password, ok = self._get_password_dialog(
            f"'{filename}' için master parolasını girin:"
        )

        if ok and password:
            self.vault_open_requested.emit(filename, password, False)

    def _quick_open(self):
        name = self.name_input.text().strip()
        password = self.password_input.text()
        secretive = self.secretive_check.isChecked()
        if not name or not password:
            QMessageBox.warning(self, "Eksik Bilgi", "Kasa adı ve parola zorunludur.")
            return

        filename = derive_vault_filename(name, password.encode(), secretive)
        full_path = os.path.join(self.vaults_dir, filename)
        if not os.path.exists(full_path):
            QMessageBox.warning(self, "Hata", "Kasa bulunamadı.")
            return

        self.vault_open_requested.emit(filename, password, secretive)

    def _create_new_vault(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Yeni Kasa Oluştur")
        dialog.setMinimumWidth(400)

        form = QFormLayout(dialog)
        form.setSpacing(12)

        name_edit = QLineEdit()
        name_edit.setMinimumHeight(36)

        pass_edit = QLineEdit()
        pass_edit.setEchoMode(QLineEdit.Password)
        pass_edit.setMinimumHeight(36)

        secret_cb = QCheckBox("Kasa adını şifrele")

        form.addRow("Kasa Adı:", name_edit)
        form.addRow("Master Parola:", pass_edit)
        form.addRow(secret_cb)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() == QDialog.Accepted:
            name = name_edit.text().strip()
            password = pass_edit.text()
            secretive = secret_cb.isChecked()
            if not name or not password:
                return

            filename = derive_vault_filename(name, password.encode(), secretive)
            full_path = os.path.join(self.vaults_dir, filename)
            if os.path.exists(full_path):
                QMessageBox.warning(self, "Hata", "Bu isimde bir kasa zaten var.")
                return

            try:
                vault = PasswordVault(name, full_path, create=True)
                vault.unlock(password.encode())
                QMessageBox.information(
                    self, "Başarılı", "Kasa başarıyla oluşturuldu ve açıldı."
                )
                self.refresh_list()
                self.vault_open_requested.emit(filename, password, secretive)

            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kasa oluşturulamadı: {e}")

    def _get_password_dialog(self, prompt):
        text, ok = QInputDialog.getText(self, "Parola", prompt, QLineEdit.Password)
        return text, ok


class EntryListWidget(QWidget):
    """Sağ panel: vault içindeki girişler."""

    entry_added = Signal(object)
    entry_updated = Signal(str, object, object)
    entry_deleted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sort_mode = SORT_NEWEST_FIRST
        self.current_entries = []  # Dosyadaki orijinal sıra (kaynak veri)
        self.displayed_entries = []  # Ekranda gösterilen (sıralanmış) hali
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Başlık + Sıralama
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title = QLabel("Kasa İçeriği")
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        title.setFont(title_font)
        title.setObjectName("section-title")
        header_layout.addWidget(title)
        header_layout.addStretch()

        sort_label = QLabel("Sırala:")
        sort_label.setStyleSheet("color: #6B7280; font-size: 10pt;")
        self.sort_combo = QComboBox()
        for value, label in SORT_OPTIONS:
            self.sort_combo.addItem(label, value)
        self.sort_combo.setMinimumHeight(32)
        self.sort_combo.setMinimumWidth(160)
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)

        header_layout.addWidget(sort_label)
        header_layout.addWidget(self.sort_combo)
        layout.addLayout(header_layout)

        # Giriş listesi
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.setUniformItemSizes(False)
        self.list_widget.setCursor(Qt.PointingHandCursor)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.add_btn = QPushButton("Ekle")
        self.add_btn.clicked.connect(self._add_entry)

        self.edit_btn = QPushButton("Düzenle")
        self.edit_btn.clicked.connect(self._edit_entry)

        self.delete_btn = QPushButton("Sil")
        self.delete_btn.clicked.connect(self._delete_entry)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

    def load_entries(self, entries: list):
        """Vault'tan gelen ham girişleri saklar ve gösterir."""
        self.current_entries = list(entries)
        self._refresh_display()

    def _get_sorted_entries(self):
        if self.sort_mode == SORT_OLDEST_FIRST:
            return list(self.current_entries)
        elif self.sort_mode == SORT_NEWEST_FIRST:
            return list(reversed(self.current_entries))
        elif self.sort_mode == SORT_BY_BADGE:
            return sorted(
                self.current_entries,
                key=lambda e: (e.data_type or "").lower(),
            )
        return list(self.current_entries)

    def _refresh_display(self):
        """Mevcut sıralama moduna göre listeyi yeniden çizer."""
        self.list_widget.clear()
        self.displayed_entries = self._get_sorted_entries()
        for entry in self.displayed_entries:
            self._add_entry_item(entry)

    def _on_sort_changed(self, index: int):
        self.sort_mode = self.sort_combo.itemData(index)
        self._refresh_display()

    def _add_entry_item(self, entry):
        """Giriş için tıklanabilir, notu açılır-kapanır liste öğesi oluşturur."""
        widget = EntryRowWidget(entry)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)

    def _on_item_clicked(self, item):
        """Satıra tıklanınca ek notu aç/kapat ve satır yüksekliğini güncelle."""
        widget = self.list_widget.itemWidget(item)
        if widget is None:
            return
        widget.toggle()
        item.setSizeHint(widget.sizeHint())

    def _selected_entry(self):
        """Seçili öğeye karşılık gelen Entry nesnesini döndürür."""
        item = self.list_widget.currentItem()
        if not item:
            return None
        idx = self.list_widget.row(item)
        if 0 <= idx < len(self.displayed_entries):
            return self.displayed_entries[idx]
        return None

    def _copy_selected(self):
        entry = self._selected_entry()
        if not entry:
            QMessageBox.warning(self, "Uyarı", "Kopyalamak için bir giriş seçin.")
            return
        copy_to_clipboard(entry.value or "")
        QMessageBox.information(
            self, "Kopyalandı", f"'{entry.name}' değeri panoya kopyalandı."
        )

    def _add_entry(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Yeni Giriş Ekle")
        dialog.setMinimumWidth(450)

        form = QFormLayout(dialog)
        form.setSpacing(12)

        name_edit = QLineEdit()
        name_edit.setMinimumHeight(36)

        type_combo = QComboBox()
        type_combo.setEditable(True)
        type_combo.addItems(list(TYPE_COLORS.keys()))
        type_combo.setMinimumHeight(36)

        value_edit = QLineEdit()
        value_edit.setMinimumHeight(36)

        note_edit = QLineEdit()
        note_edit.setMinimumHeight(36)

        form.addRow("İsim:", name_edit)
        form.addRow("Tür:", type_combo)
        form.addRow("Değer:", value_edit)
        form.addRow("Not:", note_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() == QDialog.Accepted:
            name = name_edit.text().strip()
            data_type = type_combo.currentText().strip()
            value = value_edit.text()
            note = note_edit.text()

            if not name:
                return

            entry = Entry(name, data_type, value, note)
            self.entry_added.emit(entry)

    def _edit_entry(self):
        entry = self._selected_entry()
        if not entry:
            QMessageBox.warning(self, "Uyarı", "Düzenlemek için bir giriş seçin.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Girişi Düzenle")
        dialog.setMinimumWidth(450)

        form = QFormLayout(dialog)
        form.setSpacing(12)

        value_edit = QLineEdit(entry.value or "")
        value_edit.setMinimumHeight(36)

        note_edit = QLineEdit(entry.additional_note or "")
        note_edit.setMinimumHeight(36)

        form.addRow("Yeni Değer:", value_edit)
        form.addRow("Yeni Not:", note_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() == QDialog.Accepted:
            new_value = value_edit.text() or None
            new_note = note_edit.text() or None
            self.entry_updated.emit(entry.name, new_value, new_note)

    def _delete_entry(self):
        entry = self._selected_entry()
        if not entry:
            QMessageBox.warning(self, "Uyarı", "Silmek için bir giriş seçin.")
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            f"'{entry.name}' silinsin mi?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.entry_deleted.emit(entry.name)
