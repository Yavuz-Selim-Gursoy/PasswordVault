from __future__ import annotations

import secrets
import string

UPPER = string.ascii_uppercase
LOWER = string.ascii_lowercase
DIGITS = string.digits
SYMBOLS = string.punctuation


class PasswordGenerationError(ValueError):
    """Geçersiz parametrelerle parola üretilmeye çalışıldığında fırlatılır."""


def generate_password(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
) -> str:
    """Kriptografik olarak güvenli bir parola üretir."""
    pools: list[str] = []
    if use_upper:
        pools.append(UPPER)
    if use_lower:
        pools.append(LOWER)
    if use_digits:
        pools.append(DIGITS)
    if use_symbols:
        pools.append(SYMBOLS)

    if not pools:
        raise PasswordGenerationError("En az bir karakter kümesi seçilmelidir.")

    if length < len(pools):
        raise PasswordGenerationError(
            f"Uzunluk en az {len(pools)} olmalıdır (seçili karakter kümeleri için)."
        )

    all_chars = "".join(pools)

    # Her kümeden garanti olarak bir karakter seç, kalanını tüm havuzdan doldur
    password_chars = [secrets.choice(pool) for pool in pools]
    password_chars += [secrets.choice(all_chars) for _ in range(length - len(pools))]

    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)
