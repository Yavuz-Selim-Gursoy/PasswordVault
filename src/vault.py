import base64
import json
import os
import secrets
from typing import Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from src.entry import Entry


class PasswordVault:
    def __init__(self, vault_name: str, vault_file: str, create=False):
        self.vault_name = vault_name + ":"
        self.vault_file = vault_file
        self._derived_master_key = None
        self.salt = None
        self.master_check = None

        if not os.path.exists(vault_file):
            if not create:
                raise FileNotFoundError("Vault bulunamadı.")
            self._create_new_vault()
        else:
            self._load_existing_vault()

    def _create_new_vault(self):
        self.salt = secrets.token_bytes(16)
        with open(self.vault_file, "w", encoding="ascii") as f:
            f.write("PVLT1\n")
            f.write(base64.b64encode(self.salt).decode("ascii") + "\n")
        self.master_check = None

    def _load_existing_vault(self):
        with open(self.vault_file, "r", encoding="ascii") as f:
            magic = f.readline().strip()
            if magic != "PVLT1":
                raise ValueError("Geçersiz vault formatı")

            self.salt = base64.b64decode(f.readline().strip())

            lines = [line.strip() for line in f if line.strip()]
            if len(lines) >= 2:
                self.master_check = {"nonce": lines[0], "ciphertext": lines[1]}
            else:
                self.master_check = None

    def _load_or_create_salt(self):
        if not os.path.exists(self.vault_file):
            # İlk kez vault oluşturuluyor
            self.salt = secrets.token_bytes(16)
            with open(self.vault_file, "w", encoding="ascii") as f:
                f.write("PVLT1\n")
                f.write(base64.b64encode(self.salt).decode("ascii") + "\n")
            self.master_check = None
        else:
            # Mevcut vault
            with open(self.vault_file, "r", encoding="ascii") as f:
                magic = f.readline().strip()
                if magic != "PVLT1":
                    raise ValueError("Geçersiz vault formatı")
                self.salt = base64.b64decode(f.readline().strip())
                # master_check için bir sonraki 2 satırı oku (nonce + ciphertext)
                lines = [line.strip() for line in f if line.strip()]
                if len(lines) >= 2:
                    self.master_check = {"nonce": lines[0], "ciphertext": lines[1]}
                else:
                    self.master_check = None

    def unlock(self, password: bytes):
        kdf = Scrypt(
            salt=self.salt, length=32, n=2**14, r=8, p=1, backend=default_backend()
        )
        derived_key = kdf.derive(password)

        if self.master_check is None:
            # İlk unlock = vault ilk kez açılıyor → master check oluştur
            nonce, ciphertext = self._encrypt_entry(derived_key, b"MASTER_CHECK")
            self.master_check = {"nonce": nonce, "ciphertext": ciphertext}
            with open(self.vault_file, "r+", encoding="ascii") as f:
                # Salt sonrası 2. satıra master_check ekle
                lines = f.readlines()
                lines.insert(2, nonce + "\n")
                lines.insert(3, ciphertext + "\n")
                f.seek(0)
                f.writelines(lines)
        else:
            # Var olan vault → check doğrula
            try:
                self._decrypt_entry(
                    derived_key,
                    self.master_check["nonce"],
                    self.master_check["ciphertext"],
                )
            except Exception:
                raise ValueError("Yanlış master şifre")

        self._derived_master_key = derived_key

    def _encrypt_entry(self, master_key: bytes, plaintext: bytes):
        aesgcm = AESGCM(master_key)
        nonce = secrets.token_bytes(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return (
            base64.b64encode(nonce).decode("ascii"),
            base64.b64encode(ciphertext).decode("ascii"),
        )

    def _decrypt_entry(self, master_key: bytes, nonce: str, ciphertext: str) -> bytes:
        # Nonce ve ciphertext'i base64'den decode et, derived master key ile aes'ten decrypt et.
        # Master key derived olmak zorunda.
        nonce_bytes = base64.b64decode(nonce)
        ciphertext_bytes = base64.b64decode(ciphertext)
        aesgcm = AESGCM(master_key)
        return aesgcm.decrypt(nonce_bytes, ciphertext_bytes, None)

    def add_entry(self, entry_obj: Entry) -> Entry:
        # Kasadaki entry isimlerini oku
        entry_names = [entry.name for entry in self.list_entries()]

        # Eğer zaten varsa hata fırlat
        assert entry_obj.name not in entry_names, "Nesne kasada zaten var."

        plaintext = json.dumps(
            {"v": self.vault_name, **entry_obj.to_payload()},
            ensure_ascii=False,
        ).encode("utf-8")
        nonce, ciphertext = self._encrypt_entry(self._derived_master_key, plaintext)

        # Entry nesnesinin nonce ve ciphertext'ini çıkar
        entry_obj.encryption_info["nonce"] = nonce
        entry_obj.encryption_info["ciphertext"] = ciphertext

        # Entry nesnesinin nonce ve ciphertext'ini kaydet
        with open(self.vault_file, "a", encoding="ascii") as f:
            f.write(f"{nonce}\n{ciphertext}\n")

        # Döndür ve sıfırla.
        entry_names.clear()

        return entry_obj

    def remove_entry(self, entry_name: str):
        entries = self.list_entries()
        new_entries = []
        found = False

        for e in entries:
            if e.name == entry_name:
                found = True
                continue
            new_entries.append(e)

        assert found, "Nesne kasada zaten yok."
        self._rewrite_vault(new_entries)

    def update_entry(self, entry_name: str, new_value=None, new_note=None):
        import datetime as dt

        entries = self.list_entries()
        found = False

        for e in entries:
            if e.name == entry_name:
                found = True
                if new_value is not None:
                    e.value = new_value
                if new_note is not None:
                    e.additional_note = new_note
                e.date_last_modified = dt.datetime.now()

        assert found, "Güncellenecek entry bulunamadı."

        # vault'u baştan yaz
        self._rewrite_vault(entries)

    def _rewrite_vault(self, entries):
        with open(self.vault_file, "w", encoding="ascii") as f:
            f.write("PVLT1\n")
            f.write(base64.b64encode(self.salt).decode("ascii") + "\n")
            f.write(self.master_check["nonce"] + "\n")
            f.write(self.master_check["ciphertext"] + "\n")

            for e in entries:
                plaintext = json.dumps(
                    {"v": self.vault_name, **e.to_payload()},
                    ensure_ascii=False,
                ).encode("utf-8")
                nonce, ciphertext = self._encrypt_entry(
                    self._derived_master_key, plaintext
                )
                f.write(nonce + "\n")
                f.write(ciphertext + "\n")

    def list_entries(self) -> list:
        entries = []
        try:
            with open(self.vault_file, "r", encoding="ascii") as f:
                lines = [line.strip() for line in f if line.strip()]

            # PVLT1 + salt + master_check (nonce + ciphertext)
            lines = lines[4:]

            if len(lines) % 2 != 0:
                raise ValueError("Vault dosyası bozuk: nonce/ciphertext eşleşmiyor")

            for i in range(0, len(lines), 2):
                decrypted = self._decrypt_entry(
                    self._derived_master_key, lines[i], lines[i + 1]
                )
                payload = json.loads(decrypted.decode("utf-8"))
                entry = Entry.from_payload(payload)
                entry.encryption_info["nonce"] = lines[i]
                entry.encryption_info["ciphertext"] = lines[i + 1]
                entries.append(entry)

        except FileNotFoundError:
            pass

        return entries

    def get_entry(self, entry_name: str) -> Optional[Entry]:
        # Bir vault içindeki entry'leri decrypt ederek listeler
        for entry in self.list_entries():
            if entry.name == entry_name:
                return entry
        return None
