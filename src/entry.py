import datetime as dt
import json
from typing import Optional


class Entry:
    def __init__(
        self,
        name: str,
        data_type: str = "not_specified",
        value: Optional[str] = None,
        additional_note: Optional[str] = None,
        nonce: Optional[str] = None,
        ciphertext: Optional[str] = None,
        date_added: Optional[dt.datetime] = None,
        date_last_modified: Optional[dt.datetime] = None,
    ):
        self.name = name
        self.data_type = data_type
        self.value = value
        self.additional_note = additional_note
        self.date_added = date_added or dt.datetime.now()
        self.date_last_modified = date_last_modified
        self.encryption_info = {"nonce": nonce, "ciphertext": ciphertext}

    def to_payload(self) -> dict:
        """Entry verisini JSON-serileştirilebilir dict'e dönüştürür."""
        return {
            "n": self.name,
            "t": self.data_type or "",
            "a": self.additional_note or "",
            "p": self.value or "",
            "da": self.date_added.isoformat() if self.date_added else None,
            "dm": self.date_last_modified.isoformat()
            if self.date_last_modified
            else None,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "Entry":
        """JSON payload'dan Entry nesnesi oluşturur."""
        date_added = (
            dt.datetime.fromisoformat(payload["da"]) if payload.get("da") else None
        )
        date_last_modified = (
            dt.datetime.fromisoformat(payload["dm"]) if payload.get("dm") else None
        )
        return cls(
            name=payload["n"],
            data_type=payload["t"],
            value=payload["p"],
            additional_note=payload["a"],
            date_added=date_added,
            date_last_modified=date_last_modified,
        )
