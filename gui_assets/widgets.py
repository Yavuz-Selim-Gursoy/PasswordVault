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
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.entry import Entry
from src.password_generator import PasswordGenerationError, generate_password
from src.vault import PasswordVault

from .config import (
    SORT_BY_BADGE,
    SORT_NEWEST_FIRST,
    SORT_OLDEST_FIRST,
    SORT_OPTIONS,
    TYPE_COLORS,
    scale_value,
)

# Panodaki hassas değerlerin otomatik temizlenmesi için bekleme süresi (ms)
CLIPBOARD_CLEAR_DELAY_MS = 30_000


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


def _make_row_btn(symbol: str, tooltip: str, color: str) -> QPushButton:
    """Entry satırı için küçük, sade simge butonu oluşturur."""
    btn = QPushButton(symbol)
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setMinimumHeight(scale_value(26))
    btn.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            color: {color};
            border: 1px solid {color};
            border-radius: {scale_value(10)}px;
            padding: {scale_value(2)}px {scale_value(10)}px;
            font-size: {scale_value(10)}px;
            font-weight: 600;
        }}
        QPushButton:hover  {{ background: rgba(0,0,0,15); }}
        QPushButton:pressed {{ background: rgba(0,0,0,30); }}
    """)
    return btn


class EntryTypeBadge(QLabel):
    """Giriş türü etiketi."""

    def __init__(self, data_type: str, parent=None):
        super().__init__(data_type, parent)
        color = get_color_for_type(data_type)
        self.setStyleSheet(f"""
            background-color: {color.name()};
            color: white;
            padding: {scale_value(4)}px {scale_value(12)}px;
            border-radius: {scale_value(12)}px;
            font-size: {scale_value(11)}px;
            font-weight: 600;
            letter-spacing: 0.3px;
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(scale_value(24))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.adjustSize()


class CopyButton(QPushButton):
    """Kopyala butonu.

    Tıklandığında değeri panoya kopyalar ve `CLIPBOARD_CLEAR_DELAY_MS`
    (varsayılan 30sn) sonra panoyu otomatik temizler. Bu süre içinde pano
    içeriği başka bir şeyle değiştirilmişse (örn. kullanıcı başka bir şey
    kopyaladıysa) panoya dokunulmaz; sadece hâlâ bizim kopyaladığımız değer
    duruyorsa temizlenir.

    Not: Bu, uygulamanın kendi penceresinin pano içeriğini temizler. Bazı
    masaüstü ortamları (örn. KDE Klipper) pano geçmişini ayrıca sakladığı
    için, hassas değer işletim sisteminin pano geçmişinde kalabilir. Bu,
    Qt/uygulama seviyesinde çözülemeyen bir işletim sistemi davranışıdır.
    """

    def __init__(self, value: str, parent=None):
        super().__init__("⎘", parent)
        self.value = value
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Kopyala")
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: #2563EB;
                border: 1px solid #2563EB;
                border-radius: {scale_value(10)}px;
                padding: {scale_value(2)}px {scale_value(10)}px;
                font-size: {scale_value(10)}px;
                font-weight: 600;
            }}
            QPushButton:hover  {{ background: rgba(37, 99, 235, 30); }}
            QPushButton:pressed {{ background: rgba(37, 99, 235, 60); }}
        """)
        self.clicked.connect(self._on_clicked)
        self.setMinimumHeight(scale_value(26))

    def _on_clicked(self):
        # Kopyalama işleminden sonra kısa süreli bildirim için
        copy_to_clipboard(self.value)
        original = "⎘"
        self.setText("✓")
        self.setEnabled(False)
        QTimer.singleShot(1000, lambda: (self.setText(original), self.setEnabled(True)))

        # Hassas değeri sonsuza dek panoda bırakmamak için otomatik temizleme
        copied_value = self.value
        QTimer.singleShot(
            CLIPBOARD_CLEAR_DELAY_MS,
            lambda: self._clear_clipboard_if_unchanged(copied_value),
        )

    @staticmethod
    def _clear_clipboard_if_unchanged(expected_value: str):
        """Pano hâlâ bizim kopyaladığımız değeri içeriyorsa temizler."""
        clipboard = QGuiApplication.clipboard()
        if clipboard.text() == expected_value:
            clipboard.clear()


class EntryRowWidget(QWidget):
    """Tek bir entry satırı.

    Kapalıyken: isim, değer, badge, ⎘ kopyala, ↺ düzenle, ✕ sil görünür.
    Tıklanınca detay bloğu açılır; değer ve ⎘ gizlenir, ↺ ve ✕ kalır.
    """

    edit_requested = Signal()
    delete_requested = Signal()

    def __init__(self, entry, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.expanded = False
        self.setObjectName("entry-row")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 4)
        self.main_layout.setSpacing(0)

        # --- Üst kısım (her zaman görünür) ---
        header = QWidget()
        header.setMinimumHeight(scale_value(44))
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(
            scale_value(16), scale_value(6), scale_value(12), scale_value(6)
        )
        h_layout.setSpacing(scale_value(8))

        name_label = QLabel(self.entry.name)
        name_label.setFont(QFont("Segoe UI", scale_value(10), QFont.Bold))
        name_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Değer: sadece kapalıyken görünür
        self.value_label = QLabel()
        self.value_label.setStyleSheet(
            f"color: #90A4AE; font-size: {scale_value(9)}pt;"
        )
        value_max_width = scale_value(150)
        self.value_label.setMaximumWidth(value_max_width)
        self.value_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        fm = QFontMetrics(self.value_label.font())
        elided = fm.elidedText(self.entry.value or "", Qt.ElideRight, value_max_width)
        self.value_label.setText(elided)
        if self.entry.value:
            self.value_label.setToolTip(self.entry.value)

        badge = EntryTypeBadge(self.entry.data_type)

        # ⎘ kopyala: sadece kapalıyken görünür
        self.header_copy_btn = CopyButton(self.entry.value or "")

        # ↺ düzenle ve ✕ sil: her zaman görünür
        self.edit_btn = _make_row_btn("↺", "Düzenle", "#2563EB")
        self.delete_btn = _make_row_btn("✕", "Sil", "#EF5350")
        self.edit_btn.clicked.connect(self.edit_requested.emit)
        self.delete_btn.clicked.connect(self.delete_requested.emit)

        h_layout.addWidget(name_label, 0, Qt.AlignVCenter)
        h_layout.addWidget(self.value_label, 0, Qt.AlignVCenter)
        h_layout.addStretch()
        h_layout.addWidget(badge, 0, Qt.AlignVCenter)
        h_layout.addWidget(self.header_copy_btn, 0, Qt.AlignVCenter)
        h_layout.addWidget(self.edit_btn, 0, Qt.AlignVCenter)
        h_layout.addWidget(self.delete_btn, 0, Qt.AlignVCenter)

        self.main_layout.addWidget(header)

        # --- Alt kısım: detay bloğu (kapalıyken gizli) ---
        self.detail_widget = QWidget()
        self.detail_widget.setObjectName("entry-detail")
        detail_outer_layout = QVBoxLayout(self.detail_widget)
        detail_outer_layout.setContentsMargins(0, 4, 12, 10)
        detail_outer_layout.setSpacing(0)

        # Soldan girintiyi ayarlamak için widget
        tab_container = QWidget()
        detail_layout = QVBoxLayout(tab_container)
        detail_layout.setContentsMargins(28, 10, 16, 10)
        detail_layout.setSpacing(12)

        detail_layout.addWidget(
            self._build_field_block("Etiket", self.entry.name, copyable=True)
        )
        detail_layout.addWidget(
            self._build_field_block("Değer", self.entry.value or "", copyable=True)
        )
        note_text = self.entry.additional_note or "Bu giriş için not eklenmemiş."
        detail_layout.addWidget(
            self._build_field_block("Ek Not", note_text, copyable=False)
        )

        detail_outer_layout.addWidget(tab_container)
        self.detail_widget.setVisible(False)
        self.main_layout.addWidget(self.detail_widget)

    def _build_field_block(self, title: str, content: str, copyable: bool) -> QWidget:
        """Başlık + içerik bloğunu oluşturur."""
        container = QWidget()
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(3)

        title_label = QLabel(f"{title}:")
        title_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        title_label.setObjectName("detail-field-title")
        v_layout.addWidget(title_label)

        if copyable:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            content_label = QLabel(content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet("font-size: 9pt;")

            field_copy_btn = CopyButton(content)

            row_layout.addWidget(content_label, 1)
            row_layout.addWidget(field_copy_btn, 0, Qt.AlignTop)
            v_layout.addWidget(row)
        else:
            content_label = QLabel(content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet(
                "color: #607D8B; font-style: italic; font-size: 9pt;"
            )
            v_layout.addWidget(content_label)

        return container

    def toggle(self):
        """Detay görünümünü aç/kapat."""
        self.expanded = not self.expanded
        self.detail_widget.setVisible(self.expanded)

        # Açıkken değer ve ⎘ gizlenir; ↺ ve ✕ her zaman görünür kalır.
        self.value_label.setVisible(not self.expanded)
        self.header_copy_btn.setVisible(not self.expanded)

        # Görünürlük değişikliğinden sonra layout'u zorla yeniden hesapla;
        # aksi halde sizeHint() eski değeri döndürüp elemanların
        # kesilmesine yol açabiliyor.
        self.main_layout.invalidate()
        self.main_layout.activate()
        self.updateGeometry()


class VaultRowWidget(QWidget):
    """Sol panelde tek bir kasa dosyası için sade kart görünümü."""

    def __init__(self, filename: str, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.setObjectName("vault-row")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setProperty("selected", False)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)

        name_label = QLabel(self.filename)
        name_label.setObjectName("vault-row-name")
        layout.addWidget(name_label)

    def set_selected(self, selected: bool):
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)


class VaultListWidget(QWidget):
    """Sol panel: kasa listesi ve hızlı açma formu."""

    vault_selected = Signal(str)
    vault_open_requested = Signal(str, str, bool)
    # Parola üretici modülünde "Kullan" butonuna basıldığında üretilen parolayla beraber emit edilir.
    password_use_requested = Signal(str)

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
        self.list_widget.currentItemChanged.connect(self._update_selection_styles)
        layout.addWidget(self.list_widget)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.new_btn = QPushButton("Yeni Kasa")
        self.new_btn.clicked.connect(self._create_new_vault)

        self.open_btn = QPushButton("Seçilen Kasayı Aç")
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

        # Parola Üret Bölümü
        gen_title = QLabel("Parola Üret")
        gen_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        gen_title.setObjectName("subsection-title")
        layout.addWidget(gen_title)

        # Uzunluk parçası
        length_row = QWidget()
        length_row_layout = QHBoxLayout(length_row)
        length_row_layout.setContentsMargins(0, 0, 0, 0)
        length_row_layout.setSpacing(8)

        length_label = QLabel("Uzunluk:")
        self.gen_length_spin = QSpinBox()
        self.gen_length_spin.setRange(4, 128)
        self.gen_length_spin.setValue(16)
        self.gen_length_spin.setMinimumHeight(36)

        length_row_layout.addWidget(length_label)
        length_row_layout.addWidget(self.gen_length_spin, 1)
        layout.addWidget(length_row)

        # Üretim sonucu parçası
        self.gen_result_row = QWidget()
        gen_result_layout = QHBoxLayout(self.gen_result_row)
        gen_result_layout.setContentsMargins(0, 0, 0, 0)
        gen_result_layout.setSpacing(8)

        self.gen_result_edit = QLineEdit()
        self.gen_result_edit.setReadOnly(True)
        self.gen_result_edit.setPlaceholderText("Üretilen parola burada görünecek")
        self.gen_result_edit.setMinimumHeight(36)

        # Kopyala butonu
        self.password_module_copy_btn = CopyButton(self.gen_result_edit.text() or "")

        gen_result_layout.addWidget(self.gen_result_edit)
        gen_result_layout.addWidget(self.password_module_copy_btn)
        layout.addWidget(self.gen_result_row)

        # Oluştur ve Kullan butonlarının parçası
        self.gen_create_btn = QPushButton("Oluştur")
        self.gen_create_btn.setMinimumHeight(36)
        self.gen_create_btn.clicked.connect(self._on_generate_password)
        layout.addWidget(self.gen_create_btn)

        self.gen_action_row = QWidget()
        gen_action_layout = QHBoxLayout(self.gen_action_row)
        gen_action_layout.setContentsMargins(0, 0, 0, 0)
        gen_action_layout.setSpacing(8)

        self.gen_regenerate_btn = QPushButton("Yeniden Oluştur")
        self.gen_regenerate_btn.clicked.connect(self._on_generate_password)

        self.gen_use_btn = QPushButton("Kullan")
        self.gen_use_btn.clicked.connect(self._on_use_generated_password)

        gen_action_layout.addWidget(self.gen_regenerate_btn)
        gen_action_layout.addWidget(self.gen_use_btn)
        self.gen_action_row.setVisible(False)
        layout.addWidget(self.gen_action_row)

        layout.addStretch()

    def _on_generate_password(self):
        """'Oluştur' / 'Yeniden Oluştur' butonuna basıldığında çalışır."""
        length = self.gen_length_spin.value()
        try:
            password = generate_password(length=length)
        except PasswordGenerationError as e:
            QMessageBox.warning(self, "Hata", str(e))
            return

        self.gen_result_edit.setText(password)
        # Butonlar "Oluştur" tekliden "Yeniden Oluştur" + "Kullan" ikiliye döner

        # Parola oluşturucunun yanındaki kopyalama butonu için
        self.password_module_copy_btn.value = password

        self.gen_create_btn.setVisible(False)
        self.gen_action_row.setVisible(True)

    def _on_use_generated_password(self):
        """'Kullan' butonuna basıldığında üretilen parolayı dışarı bildirir."""
        password = self.gen_result_edit.text()
        if not password:
            return
        self.password_use_requested.emit(password)

    def refresh_list(self):
        """Vault dosyalarını listeler."""
        self.list_widget.clear()
        if not os.path.exists(self.vaults_dir):
            os.makedirs(self.vaults_dir)

        for f in sorted(os.listdir(self.vaults_dir)):
            if f.endswith(".pvlt"):
                item = QListWidgetItem()
                item.setData(Qt.UserRole, f)
                widget = VaultRowWidget(f)
                item.setSizeHint(widget.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)

    def _update_selection_styles(self, current, previous):
        if previous is not None:
            widget = self.list_widget.itemWidget(previous)
            if widget is not None:
                widget.set_selected(False)
        if current is not None:
            widget = self.list_widget.itemWidget(current)
            if widget is not None:
                widget.set_selected(True)

    def _open_selected_vault(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "Uyarı", "Lütfen listeden bir kasa seçin.")
            return

        filename = item.data(Qt.UserRole)
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

        # Başlık + Sıralama + Ekle butonu
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.title_label = QLabel("Kasa İçeriği")
        self.title_label.setFont(QFont("Segoe UI", scale_value(18), QFont.Bold))
        self.title_label.setObjectName("section-title")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.sort_label = QLabel("Sırala:")
        self.sort_label.setStyleSheet(
            f"color: #6B7280; font-size: {scale_value(10)}pt;"
        )
        self.sort_combo = QComboBox()
        for value, label in SORT_OPTIONS:
            self.sort_combo.addItem(label, value)
        self.sort_combo.setMinimumHeight(scale_value(32))
        self.sort_combo.setMinimumWidth(scale_value(160))
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)

        # Ekle butonu: dropdown'ın hemen yanında
        self.add_btn = QPushButton("+")
        self.add_btn.setToolTip("Yeni giriş ekle")
        self.add_btn.setMinimumHeight(scale_value(32))
        self.add_btn.setFixedWidth(scale_value(36))
        self.add_btn.clicked.connect(lambda: self._add_entry())

        header_layout.addWidget(self.sort_label)
        header_layout.addWidget(self.sort_combo)
        header_layout.addWidget(self.add_btn)
        layout.addLayout(header_layout)

        # Giriş listesi
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.setUniformItemSizes(False)
        self.list_widget.setCursor(Qt.PointingHandCursor)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

    def apply_scale(self):
        """Ölçek değiştiğinde başlık/etiket/buton boyutlarını günceller
        ve satırları yeni ölçekle yeniden çizer."""
        self.title_label.setFont(QFont("Segoe UI", scale_value(18), QFont.Bold))
        self.sort_label.setStyleSheet(
            f"color: #6B7280; font-size: {scale_value(10)}pt;"
        )
        self.sort_combo.setMinimumHeight(scale_value(32))
        self.sort_combo.setMinimumWidth(scale_value(160))
        self.add_btn.setMinimumHeight(scale_value(32))
        self.add_btn.setFixedWidth(scale_value(36))
        self._refresh_display()

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
        widget.edit_requested.connect(lambda e=entry: self._edit_entry(e))
        widget.delete_requested.connect(lambda e=entry: self._delete_entry(e))
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)

    def _on_item_clicked(self, item):
        """Satıra tıklanınca detay bloğunu aç/kapat ve satır yüksekliğini güncelle."""
        widget = self.list_widget.itemWidget(item)
        if widget is None:
            return
        widget.toggle()
        item.setSizeHint(widget.sizeHint())

    def open_add_entry_dialog(self, initial_value: str | None = None):
        """Yeni giriş diyalogunu dışarıdan (örn. parola üretici modülünden)
        açmak için kullanılan public metod."""
        self._add_entry(initial_value=initial_value)

    def _add_entry(self, initial_value: str | None = None):
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
        if initial_value:
            # Dışarıdan üretilmiş bir parola geldiyse türü otomatik "password" yap
            password_index = type_combo.findText("password")
            if password_index >= 0:
                type_combo.setCurrentIndex(password_index)

        value_edit = QLineEdit(initial_value or "")
        value_edit.setMinimumHeight(36)

        gen_btn = QPushButton("⚄")
        gen_btn.setToolTip("Parola Üret")
        gen_btn.setFixedWidth(40)
        gen_btn.setMinimumHeight(36)
        gen_btn.clicked.connect(
            lambda: self._open_password_generator_dialog(value_edit)
        )

        value_row = QWidget()
        value_row_layout = QHBoxLayout(value_row)
        value_row_layout.setContentsMargins(0, 0, 0, 0)
        value_row_layout.setSpacing(6)
        value_row_layout.addWidget(value_edit)
        value_row_layout.addWidget(gen_btn)

        note_edit = QLineEdit()
        note_edit.setMinimumHeight(36)

        form.addRow("İsim:", name_edit)
        form.addRow("Tür:", type_combo)
        form.addRow("Değer:", value_row)
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

    def _open_password_generator_dialog(self, target_edit: QLineEdit):
        """Parola üretici parametrelerini sorar ve sonucu hedef alana yazar."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Parola Üret")
        dialog.setMinimumWidth(350)

        form = QFormLayout(dialog)
        form.setSpacing(12)

        length_spin = QSpinBox()
        length_spin.setRange(4, 128)
        length_spin.setValue(16)

        upper_cb = QCheckBox("Büyük harf (A-Z)")
        upper_cb.setChecked(True)
        lower_cb = QCheckBox("Küçük harf (a-z)")
        lower_cb.setChecked(True)
        digits_cb = QCheckBox("Rakam (0-9)")
        digits_cb.setChecked(True)
        symbols_cb = QCheckBox("Sembol (!@#$...)")
        symbols_cb.setChecked(True)

        form.addRow("Uzunluk:", length_spin)
        form.addRow(upper_cb)
        form.addRow(lower_cb)
        form.addRow(digits_cb)
        form.addRow(symbols_cb)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() == QDialog.Accepted:
            try:
                password = generate_password(
                    length=length_spin.value(),
                    use_upper=upper_cb.isChecked(),
                    use_lower=lower_cb.isChecked(),
                    use_digits=digits_cb.isChecked(),
                    use_symbols=symbols_cb.isChecked(),
                )
            except PasswordGenerationError as e:
                QMessageBox.warning(self, "Hata", str(e))
                return
            target_edit.setText(password)

    def _edit_entry(self, entry):
        """Verilen entry için düzenleme dialogunu açar."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Girişi Düzenle")
        dialog.setMinimumWidth(450)

        form = QFormLayout(dialog)
        form.setSpacing(12)

        value_edit = QLineEdit(entry.value or "")
        value_edit.setMinimumHeight(36)

        gen_btn = QPushButton("⚄")
        gen_btn.setToolTip("Parola Üret")
        gen_btn.setFixedWidth(40)
        gen_btn.setMinimumHeight(36)
        gen_btn.clicked.connect(
            lambda: self._open_password_generator_dialog(value_edit)
        )

        value_row = QWidget()
        value_row_layout = QHBoxLayout(value_row)
        value_row_layout.setContentsMargins(0, 0, 0, 0)
        value_row_layout.setSpacing(6)
        value_row_layout.addWidget(value_edit)
        value_row_layout.addWidget(gen_btn)

        note_edit = QLineEdit(entry.additional_note or "")
        note_edit.setMinimumHeight(36)

        form.addRow("Yeni Değer:", value_row)
        form.addRow("Yeni Not:", note_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() == QDialog.Accepted:
            new_value = value_edit.text() or None
            new_note = note_edit.text() or None
            self.entry_updated.emit(entry.name, new_value, new_note)

    def _delete_entry(self, entry):
        """Verilen entry için silme onayı ister ve siler."""
        reply = QMessageBox.question(
            self,
            "Onay",
            f"'{entry.name}' silinsin mi?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.entry_deleted.emit(entry.name)
