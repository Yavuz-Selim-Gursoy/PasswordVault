import datetime as dt
from typing import Optional

class Entry:
    def __init__(self, name: str, data_type: str = "not_specified", value: Optional[str] = None, additional_note: Optional[str] = None, nonce: Optional[str] = None, ciphertext: Optional[str] = None):
        self.name = name
        self.data_type = data_type
        self.value = value  # gerçek veri
        self.additional_note = additional_note
        self.date_added = dt.datetime.now()
        self.date_last_modified = None

        self.encryption_info = {"nonce": nonce, "ciphertext": ciphertext}

    def to_plaintext_bytes(self, vault_name: str) -> bytes:
        """
        Metadata + gerçek veri birleştirilip encrypt için bytes olarak döndürülür
        """
        parts = [vault_name.encode("utf-8"), self.name.encode("utf-8"), self.data_type.encode("utf-8"), (self.additional_note or "").encode("utf-8"), (self.value or "").encode("utf-8")]
        return b"|".join(parts)