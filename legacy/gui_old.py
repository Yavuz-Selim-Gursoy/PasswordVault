import base64
import hashlib
import os
import sys
from typing import Optional

from PyQt5 import QtCore, QtWidgets

from src.vault import Entry, PasswordVault


def derive_vault_filename(vault_name: str, password: bytes) -> str:
    h = hashlib.blake2b(
        vault_name.encode("utf-8"), key=password, digest_size=16
    ).digest()
    fn = base64.urlsafe_b64encode(h).decode("ascii") + ".pvlt"
    # Vaults klasörü proje içindeki PasswordVault dizini altında
    base = os.path.dirname(__file__)
    return os.path.join(base, "vaults", fn)


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vault Girişi")
        self.resize(320, 120)

        self.name_edit = QtWidgets.QLineEdit()
        self.pass_edit = QtWidgets.QLineEdit()
        self.pass_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.create_check = QtWidgets.QCheckBox("Yoksa oluştur")

        form = QtWidgets.QFormLayout()
        form.addRow("Vault adı:", self.name_edit)
        form.addRow("Parola:", self.pass_edit)
        form.addRow("", self.create_check)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        lay = QtWidgets.QVBoxLayout()
        lay.addLayout(form)
        lay.addWidget(btns)
        self.setLayout(lay)

    def get_values(self):
        return (
            self.name_edit.text().strip(),
            self.pass_edit.text().encode(),
            self.create_check.isChecked(),
        )


class EntryDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, entry: Optional[Entry] = None):
        super().__init__(parent)
        self.setWindowTitle("Entry")
        self.resize(400, 180)

        self.name = QtWidgets.QLineEdit()
        self.type = QtWidgets.QLineEdit()
        self.value = QtWidgets.QLineEdit()
        self.note = QtWidgets.QLineEdit()

        form = QtWidgets.QFormLayout()
        form.addRow("Ad:", self.name)
        form.addRow("Tür:", self.type)
        form.addRow("Değer:", self.value)
        form.addRow("Not:", self.note)

        if entry:
            self.name.setText(entry.name)
            self.type.setText(entry.data_type)
            self.value.setText(entry.value or "")
            self.note.setText(entry.additional_note or "")
            self.name.setEnabled(False)  # isim değişmez

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        lay = QtWidgets.QVBoxLayout()
        lay.addLayout(form)
        lay.addWidget(btns)
        self.setLayout(lay)

    def get_entry(self):
        return Entry(
            self.name.text().strip(),
            self.type.text().strip(),
            value=self.value.text(),
            additional_note=self.note.text(),
        )


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Password Vault GUI")
        self.resize(800, 480)

        self.vault = None

        # Widgets
        self.list_widget = QtWidgets.QListWidget()
        self.detail = QtWidgets.QTextEdit()
        self.detail.setReadOnly(True)

        # Buttons
        btn_add = QtWidgets.QPushButton("Add")
        btn_update = QtWidgets.QPushButton("Update")
        btn_remove = QtWidgets.QPushButton("Remove")
        btn_switch = QtWidgets.QPushButton("Switch Vault")
        btn_refresh = QtWidgets.QPushButton("Refresh")
        btn_exit = QtWidgets.QPushButton("Exit")

        btn_add.clicked.connect(self.add_entry)
        btn_update.clicked.connect(self.update_entry)
        btn_remove.clicked.connect(self.remove_entry)
        btn_switch.clicked.connect(self.switch_vault)
        btn_refresh.clicked.connect(self.refresh_entries)
        btn_exit.clicked.connect(self.close)

        self.list_widget.currentItemChanged.connect(self.show_selected_entry)

        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(self.list_widget)
        left_layout.addWidget(btn_refresh)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(self.detail)

        hsplit = QtWidgets.QSplitter()
        left_container = QtWidgets.QWidget()
        left_container.setLayout(left_layout)
        right_container = QtWidgets.QWidget()
        right_container.setLayout(right_layout)
        hsplit.addWidget(left_container)
        hsplit.addWidget(right_container)

        btn_bar = QtWidgets.QHBoxLayout()
        btn_bar.addWidget(btn_add)
        btn_bar.addWidget(btn_update)
        btn_bar.addWidget(btn_remove)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_switch)
        btn_bar.addWidget(btn_exit)

        central = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(hsplit)
        main_layout.addLayout(btn_bar)
        central.setLayout(main_layout)

        self.setCentralWidget(central)

        # Prompt for initial vault
        QtCore.QTimer.singleShot(0, self.switch_vault)

    def switch_vault(self):
        dlg = LoginDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            name, password, create_flag = dlg.get_values()
            if not name or not password:
                QtWidgets.QMessageBox.warning(
                    self, "Hata", "Vault adı ve parola gerekli"
                )
                return

            vault_file = derive_vault_filename(name, password)
            try:
                # vault_file path artık absolute; kontrol için os.path.exists kullan
                if create_flag or not os.path.exists(vault_file):
                    vault = PasswordVault(name, vault_file, create=True)
                else:
                    vault = PasswordVault(name, vault_file)
                vault.unlock(password)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Açma hatası", str(e))
                return

            self.vault = vault
            self.setWindowTitle(f"Password Vault GUI - {name}")
            self.refresh_entries()

    def refresh_entries(self):
        self.list_widget.clear()
        if not self.vault:
            return
        try:
            entries = self.vault.list_entries()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Entries listelenemedi: {e}")
            return

        for e in entries:
            item = QtWidgets.QListWidgetItem(f"{e.name} ({e.data_type})")
            item.setData(QtCore.Qt.UserRole, e)
            self.list_widget.addItem(item)

    def show_selected_entry(self, current, previous):
        if current is None:
            self.detail.clear()
            return
        entry = current.data(QtCore.Qt.UserRole)
        if not entry:
            self.detail.clear()
            return
        text = f"Ad: {entry.name}\nTür: {entry.data_type}\nDeğer: {entry.value}\nNot: {entry.additional_note}\n"
        self.detail.setPlainText(text)

    def add_entry(self):
        if not self.vault:
            QtWidgets.QMessageBox.warning(self, "Hata", "Önce vault açın")
            return
        dlg = EntryDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            entry = dlg.get_entry()
            try:
                self.vault.add_entry(entry)
                QtWidgets.QMessageBox.information(self, "Tamam", "Entry eklendi")
                self.refresh_entries()
            except AssertionError as ex:
                QtWidgets.QMessageBox.warning(self, "Hata", str(ex))

    def update_entry(self):
        if not self.vault:
            QtWidgets.QMessageBox.warning(self, "Hata", "Önce vault açın")
            return
        item = self.list_widget.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, "Hata", "Önce bir entry seçin")
            return
        entry = item.data(QtCore.Qt.UserRole)
        dlg = EntryDialog(self, entry=entry)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            new_e = dlg.get_entry()
            try:
                # Only update value and note
                self.vault.update_entry(
                    entry.name, new_value=new_e.value, new_note=new_e.additional_note
                )
                QtWidgets.QMessageBox.information(self, "Tamam", "Entry güncellendi")
                self.refresh_entries()
            except AssertionError as ex:
                QtWidgets.QMessageBox.warning(self, "Hata", str(ex))

    def remove_entry(self):
        if not self.vault:
            QtWidgets.QMessageBox.warning(self, "Hata", "Önce vault açın")
            return
        item = self.list_widget.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, "Hata", "Önce bir entry seçin")
            return
        entry = item.data(QtCore.Qt.UserRole)
        ans = QtWidgets.QMessageBox.question(
            self,
            "Sil",
            f"'{entry.name}' silinsin mi?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if ans == QtWidgets.QMessageBox.Yes:
            try:
                self.vault.remove_entry(entry.name)
                QtWidgets.QMessageBox.information(self, "Tamam", "Entry silindi")
                self.refresh_entries()
            except AssertionError as ex:
                QtWidgets.QMessageBox.warning(self, "Hata", str(ex))


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
