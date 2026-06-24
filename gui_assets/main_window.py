import base64
import hashlib
import os

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.vault import PasswordVault

from .config import THEMES, apply_theme
from .widgets import EntryListWidget, VaultListWidget


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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parola Kasası")
        self.resize(1200, 700)

        # Ekranı ortala
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 1200) // 2
        y = (screen.height() - 700) // 2
        self.move(x, y)

        # Ayarları yükle
        self.settings = QSettings("PasswordVault", "GUI")
        self.current_theme = self.settings.value("theme", "light")

        # Aktif vault
        self.active_vault: PasswordVault = None
        self.vaults_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "vaults"
        )

        self._init_ui()
        self._apply_theme(self.current_theme)
        self.showMaximized()

    def _init_ui(self):
        """Arayüzü oluştur."""
        # Menü çubuğu
        menubar = self.menuBar()
        menubar.setStyleSheet("spacing: 8px; padding: 4px;")

        theme_menu = menubar.addMenu("Tema")
        for key, theme in THEMES.items():
            action = theme_menu.addAction(theme["name"])
            action.setData(key)
            action.triggered.connect(self._change_theme)

        # Merkez widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter (sol-sağ)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background: #E0E0E0; }")

        # Sol panel
        self.vault_panel = VaultListWidget(self.vaults_dir)
        self.vault_panel.vault_open_requested.connect(self._open_vault_from_request)

        # Sağ panel
        self.entry_panel = EntryListWidget()
        self.entry_panel.entry_added.connect(self._add_entry_to_vault)
        self.entry_panel.entry_updated.connect(self._update_entry_in_vault)
        self.entry_panel.entry_deleted.connect(self._delete_entry_from_vault)

        self.splitter.addWidget(self.vault_panel)
        self.splitter.addWidget(self.entry_panel)
        self.splitter.setSizes([250, 750])

        main_layout.addWidget(self.splitter)

        # Başlangıçta sağ panel deaktif
        self.entry_panel.setEnabled(False)

    def _resizeEvent(self, event):
        super().resizeEvent(event)
        total_width = self.splitter.width()
        if total_width <= 0:
            return

        left_ratio = 0.2
        right_ratio = 0.8

        left_width = int(total_width * left_ratio)
        right_width = total_width - left_width

        # Splitter'ı bu orana zorla
        self.splitter.setSizes([left_width, right_width])

    def _change_theme(self):
        """Temayı değiştirir."""
        action = self.sender()
        theme_name = action.data()
        self.current_theme = theme_name
        self._apply_theme(theme_name)
        self.settings.setValue("theme", theme_name)

    def _apply_theme(self, theme_name: str):
        """Tema uygular."""
        apply_theme(QApplication.instance(), theme_name)
        # Dark temada splitter handle'ı daha açık yap
        if theme_name == "dark":
            self.splitter.setStyleSheet("QSplitter::handle { background: #334155; }")
        elif theme_name == "ocean":
            self.splitter.setStyleSheet("QSplitter::handle { background: #7DD3FC; }")
        else:
            self.splitter.setStyleSheet("QSplitter::handle { background: #E5E7EB; }")

    def _open_vault_from_request(self, filename: str, password: str, secretive: bool):
        """Vault'u açmayı dener."""
        filepath = os.path.join(self.vaults_dir, filename)
        if not os.path.exists(filepath):
            QMessageBox.warning(self, "Hata", "Kasa dosyası bulunamadı.")
            return

        try:
            vault_name_guess = os.path.splitext(filename)[0]
            vault = PasswordVault(vault_name_guess, filepath)
            vault.unlock(password.encode())
            self._set_active_vault(vault)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kasa açılamadı: {e}")

    def _set_active_vault(self, vault: PasswordVault):
        """Aktif vault'u ayarlar."""
        self.active_vault = vault
        entries = vault.list_entries()
        self.entry_panel.load_entries(entries)
        self.entry_panel.setEnabled(True)

        # Başlığı güncelle
        vault_filename = os.path.basename(vault.vault_file)
        self.setWindowTitle(f"Parola Kasası — {vault_filename}")

        # Sol panelde seçimi güncelle
        for i in range(self.vault_panel.list_widget.count()):
            list_item = self.vault_panel.list_widget.item(i)
            if list_item.data(Qt.UserRole) == vault_filename:
                self.vault_panel.list_widget.setCurrentItem(list_item)
                break

    def _add_entry_to_vault(self, entry):
        """Giriş ekler."""
        if not self.active_vault:
            return

        try:
            self.active_vault.add_entry(entry)
            self._refresh_entries()
            QMessageBox.information(self, "Başarılı", "Giriş başarıyla eklendi.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _update_entry_in_vault(self, name, new_value, new_note):
        """Girişi günceller."""
        if not self.active_vault:
            return

        try:
            self.active_vault.update_entry(name, new_value, new_note)
            self._refresh_entries()
            QMessageBox.information(self, "Başarılı", "Giriş başarıyla güncellendi.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _delete_entry_from_vault(self, name):
        """Girişi siler."""
        if not self.active_vault:
            return

        try:
            self.active_vault.remove_entry(name)
            self._refresh_entries()
            QMessageBox.information(self, "Başarılı", "Giriş başarıyla silindi.")

        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _refresh_entries(self):
        """Giriş listesini günceller."""
        if self.active_vault:
            entries = self.active_vault.list_entries()
            self.entry_panel.load_entries(entries)
