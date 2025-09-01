import re
import phonenumbers

DEFAULT_REGION = "IR"

def normalize_phone(raw: str) -> str | None:
    if not raw:
        return None
    candidate = (raw or "").strip()
    candidate = re.sub(r"[\s\-()]+", "", candidate)
    try:
        parsed = phonenumbers.parse(candidate, DEFAULT_REGION)
        if not phonenumbers.is_valid_number(parsed):
            return None
        e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        return e164
    except Exception:
        return None
