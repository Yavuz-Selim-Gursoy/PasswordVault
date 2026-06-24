import base64
import hashlib
import os

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QActionGroup
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

from . import config
from .config import DEFAULT_SCALE, SCALE_OPTIONS, THEMES, apply_theme
from .widgets import EntryListWidget, VaultListWidget

# Aktif kasa hiçbir manuel kapatma olmadan açıldıktan kaç ms sonra otomatik
# kilitlenir (5 dakika).
VAULT_AUTO_LOCK_MS = 5 * 60 * 1000


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

        loaded_scale = self.settings.value("scale", DEFAULT_SCALE)
        try:
            loaded_scale = int(loaded_scale)
        except (TypeError, ValueError):
            loaded_scale = DEFAULT_SCALE
        self.current_scale = (
            loaded_scale if loaded_scale in SCALE_OPTIONS else DEFAULT_SCALE
        )
        # widgets.py içindeki widget'lar oluşturulurken bu değeri okuyacağı
        # için _init_ui() çağrılmadan ÖNCE ayarlanması gerekiyor.
        config.set_current_scale(self.current_scale)

        # Aktif vault
        self.active_vault: PasswordVault = None
        self.vaults_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "vaults"
        )

        # Kasa otomatik kilitleme zamanlayıcısı
        self._vault_lock_timer = QTimer(self)
        self._vault_lock_timer.setSingleShot(True)
        self._vault_lock_timer.timeout.connect(self._auto_lock_vault)

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

        scale_menu = menubar.addMenu("Ölçek")
        self._scale_action_group = QActionGroup(self)
        self._scale_action_group.setExclusive(True)
        for s in SCALE_OPTIONS:
            action = scale_menu.addAction(f"%{s}")
            action.setData(s)
            action.setCheckable(True)
            action.setChecked(s == self.current_scale)
            action.triggered.connect(self._change_scale)
            self._scale_action_group.addAction(action)

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

    def _change_scale(self):
        """Arayüz/asset ölçeğini değiştirir."""
        action = self.sender()
        scale = action.data()
        self.current_scale = scale
        config.set_current_scale(scale)

        # Tema QSS'ini yeni ölçekle yeniden uygula
        self._apply_theme(self.current_theme)

        # Sabit boyutlarla oluşturulmuş entry satırlarını / başlık-buton
        # boyutlarını yeniden çiz
        self.entry_panel.apply_scale()

        self.settings.setValue("scale", scale)

    def _apply_theme(self, theme_name: str):
        """Tema uygular."""
        apply_theme(QApplication.instance(), theme_name, self.current_scale)
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

        # Kasa açıldığı andan itibaren otomatik kilitleme geri sayımını başlat
        self._vault_lock_timer.stop()
        self._vault_lock_timer.start(VAULT_AUTO_LOCK_MS)

    def _auto_lock_vault(self):
        """VAULT_AUTO_LOCK_MS süresi dolduğunda aktif kasayı otomatik kapatır.

        Not: Bu süre kullanıcı etkinliğiyle sıfırlanmaz; kasa açıldığı
        andan itibaren sabit bir geri sayımdır.
        """
        if not self.active_vault:
            return

        self.active_vault = None
        self.entry_panel.load_entries([])
        self.entry_panel.setEnabled(False)
        self.setWindowTitle("Parola Kasası")
        self.vault_panel.list_widget.clearSelection()

        QMessageBox.information(
            self,
            "Kasa Kilitlendi",
            "Kasa, açıldıktan 5 dakika sonra güvenlik amacıyla otomatik olarak kapatılır. İşleminize devam etmek için kasayı yeniden açın.",
        )

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
