# PasswordVault

PasswordVault, Python ile yazılmış, dosya tabanlı basit bir parola kasasıdır. Vault içindeki veriler scrypt ile türetilen bir anahtar kullanılarak AES-GCM ile şifrelenir. Bu proje geliştirme ve test amaçlıdır; kritik veriler için doğrudan kullanılmamalıdır.

## UYARI — SORUMLULUK REDDİ

- Bu yazılım sadece test amaçlıdır; kritik veriler için doğrudan **KULLANILMAMALIDIR**.
- Kullanıcı sisteminin ve parola kasalarının yedeklerini güvenli bir yerde saklamalıdır.
- Kullanıcı kasaların parolalarını unutmamalıdır. Ana parola kaybı veri kurtarmayı imkansız hale getirebilir.
- Kullanıcı uygulamayı kullanarak verilerinin silinmesi, bozulması veya erişilemez hale gelmesi riskini kabul eder. Herhangi bir mağduriyet durumunda proje sahipleri, katkıda bulunanlar veya sağlayıcılar hiçbir sorumluluk kabul etmez.
- Yazılım mümkünse izole bir makinede veya güvenilir, sınırlı bir ağ içinde çalıştırılmalıdır. Paylaşılan ve halka açık ortamlarda kullanmak riskleri artıracaktır.

## NASIL ÇALIŞIR?

- Her vault tek bir dosyada saklanır; dosyalar proje içindeki `vaults/` dizininde bulunur.
- Vault dosyası adı, vault adı ve parola kombinasyonundan türetilir (hash + base64) ve `.pvlt` uzantısı alır.
- Dosya formatı (kısaca):
  - Başlık: `PVLT1`
  - İkinci satır: Base64 kodlu salt
  - İsteğe bağlı: master-check için nonce + ciphertext (parola doğrulama)
  - Ardından her entry için iki satır: nonce, ciphertext (her ikisi de Base64)
- Anahtar türetme: scrypt (varsayılan parametreler: n=2**14, r=8, p=1)
- Şifreleme: AES-GCM (cryptography kütüphanesi kullanılır)
- Entry verisi ve metadata, `|` ile birleştirilip byte olarak şifrelenir; deşifre edildiğinde parçalara ayrılarak kullanılır.

## HIZLI BAŞLANGIÇ

1. Sanal ortam oluşturun ve etkinleştirin:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. Veri dizinini oluşturun (vaults/):
   ```bash
   python3 src/create_dirs.py
   ```

4. Kütüphane örneği (Python REPL veya küçük bir runner):

    ```python
    from src.vault import PasswordVault, Entry
    
    vault_file = "vaults/myvault.pvlt"
    vault = PasswordVault("myvault", vault_file, create=True)
    vault.unlock(b"password")
    entry = Entry("example", "password", value="s3cr3t", additional_note="demo")
    vault.add_entry(entry)
    print(vault.list_entries())
    ```

## DOSYA YAPISI

- `src/entry.py` — Entry modeli ve serileştirme yardımcıları
- `src/vault.py` — PasswordVault sınıfı: vault oluşturma, yükleme, anahtar türetme, şifreleme/çözme ve entry yönetimi
- `src/create_dirs.py` — Vault dizinini oluşturmak için yardımcı script
- CLI ve GUI frontendlere çalışma dizininde erişilebilir; ancak bu frontendlere ilişkin detaylar ayrı commit/branch'larda tutulmuştur

## NOTLAR
Proje sadece Python ve herhangi bir işletim sistemi üzerinde çalıştırılmak üzere oluşturulmuştur. İleride özel bir donanım geliştirilerek güvenlik önlemlerinin artırılması planlanmaktadır. Ek olarak, güvenlik önlemlerinin sınırlı olduğu ancak kullanım kolaylığı sağlayan çeşitli yöntemler de izlenebilir.
