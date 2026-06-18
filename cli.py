import base64
import getpass
import hashlib
import os
from typing import Optional

from src.vault import Entry, PasswordVault


def derive_vault_filename(
    vault_name: str, password: bytes, secretive: bool = True
) -> str:
    h = hashlib.blake2b(
        vault_name.encode("utf-8"), key=password, digest_size=16
    ).digest()
    if secretive:
        fn = base64.urlsafe_b64encode(h).decode("ascii") + ".pvlt"
    elif not secretive:
        fn = vault_name + ".pvlt"
    base = os.path.dirname(__file__)
    return os.path.join(base, "vaults", fn)


def vault_select() -> Optional[PasswordVault]:
    base = os.path.dirname(__file__)
    vaults_dir = os.path.join(base, "vaults")
    os.makedirs(vaults_dir, exist_ok=True)

    # Mevcut vault dosyalarını listele
    vault_files = [f for f in os.listdir(vaults_dir) if f.endswith(".pvlt")]
    if vault_files:
        print("Mevcut kasalar:")
        for i, fn in enumerate(vault_files, start=1):
            print(f"  {i}. {fn}")

        choice = input("Açmak için numara girin veya 'n' ile yeni oluşturun: ").strip()
        if choice.lower() == "n":
            # Yeni vault oluşturma akışı
            vault_name = input("Vault adı: ")
            password = getpass.getpass("Vault parolası: ").encode()
            secretive_input = str(input("Vault ismini gizlemek ister misiniz? (y/n)"))
            if secretive_input.lower() == "y":
                secretive = True
            else:
                secretive = False
            vault_file = derive_vault_filename(vault_name, password, secretive)

            try:
                if os.path.exists(vault_file):
                    vault = PasswordVault(vault_name, vault_file)
                else:
                    ans = input("Vault yok. Yeni oluşturulsun mu? (y/n): ")
                    if ans.lower() != "y":
                        return None
                    vault = PasswordVault(vault_name, vault_file, create=True)

                vault.unlock(password)
                print("Vault başarıyla açıldı.")
                return vault
            except ValueError:
                print("Yanlış parola.")
                return None
        else:
            # Numara ile seçim
            try:
                idx = int(choice) - 1
                selected = vault_files[idx]
            except Exception:
                print("Geçersiz seçim.")
                return None

            vault_file_path = os.path.join(vaults_dir, selected)
            # Vault adı bilinmediği için dosya adı tabanını isim olarak kullanıyoruz
            vault_name_guess = os.path.splitext(selected)[0]
            password = getpass.getpass(f"{selected} için parola: ").encode()
            try:
                vault = PasswordVault(vault_name_guess, vault_file_path)
                vault.unlock(password)
                print("Vault başarıyla açıldı.")
                return vault
            except Exception as e:
                print(f"Açma hatası: {e}")
                return None

    # Eğer vault yoksa veya listede yoksa klasik akışa dön
    vault_name = input("Vault adı: ")

    while True:
        password = getpass.getpass("Vault parolası: ").encode()
        secretive_input = str(input("Vault ismini gizlemek ister misiniz? (y/n)"))
        if secretive_input.lower() == "y":
            secretive = True
        else:
            secretive = False
        vault_file = derive_vault_filename(vault_name, password, secretive)

        try:
            if os.path.exists(vault_file):
                vault = PasswordVault(vault_name, vault_file)
            else:
                ans = input("Vault yok. Yeni oluşturulsun mu? (y/n): ")
                if ans.lower() != "y":
                    return
                vault = PasswordVault(vault_name, vault_file, create=True)

            vault.unlock(password)
            print("Vault başarıyla açıldı.")
            return vault
            break

        except ValueError:
            print("Yanlış parola. Tekrar deneyin.")
        except FileNotFoundError as e:
            print(e)


def mainloop(vault: Optional[PasswordVault]):
    if not vault:
        print("Vault açılmadı. Çıkılıyor.")
        return

    while True:
        cmd = input("> ").strip().lower()

        if cmd == "list":
            entries = vault.list_entries()
            if not entries:
                print("Vault boş.")
            for e in entries:
                print(
                    f"- {e.name}: {e.value} ({e.data_type}) Note: {e.additional_note}"
                )

        elif cmd == "add":
            name = input("Entry adı: ")
            data_type = input("Tür (password, username, note vb.): ")
            value = input("Değer: ")
            note = input("Ek not (isteğe bağlı): ")
            entry = Entry(name, data_type, value=value, additional_note=note)
            try:
                vault.add_entry(entry)
                print(f"'{name}' eklendi.")
            except AssertionError as ex:
                print(ex)

        elif cmd == "update":
            name = input("Güncellenecek entry adı: ")
            value = input("Yeni değer (boş bırakılırsa değişmez): ")
            note = input("Yeni not (boş bırakılırsa değişmez): ")
            value = value if value else None
            note = note if note else None
            try:
                vault.update_entry(name, new_value=value, new_note=note)
                print(f"'{name}' güncellendi.")
            except AssertionError as ex:
                print(ex)

        elif cmd == "remove":
            name = input("Silinecek entry adı: ")
            try:
                vault.remove_entry(name)
                print(f"'{name}' silindi.")
            except AssertionError as ex:
                print(ex)

        elif cmd == "get":
            name = input("Görüntülenecek entry adı: ")
            entry = vault.get_entry(name)
            if entry:
                print(
                    f"{entry.name}: {entry.value} ({entry.data_type}) Note: {entry.additional_note}"
                )
            else:
                print("Entry bulunamadı.")

        elif cmd == "switch":
            new_vault = vault_select()
            if new_vault:
                vault = new_vault
                print("Vault değiştirildi.")
            else:
                print("Vault değiştirme iptal edildi.")

        elif cmd == "exit":
            print("Çıkış yapılıyor.")
            break

        elif cmd == "help":
            print("""\nKomut listesi:
            list: Kasada bulunan parolaları listeler.
            add: Kasaya yeni bir girdi ekler.
            update: Kasadaki bir girdinin değerini değiştirir.
            get: Kasadaki tek bir girdiyi ekrana yazdırır.
            switch: Kasayı değiştirir.
            help: Komutları listeler.
            """)

        else:
            print("Bilinmeyen komut.")


def run_cli():

    print("=== Password Vault CLI ===")

    print("""\nKomutlar:
            list, add, update, remove, get, switch, help, exit\n""")

    mainloop(vault_select())


if __name__ == "__main__":
    run_cli()
