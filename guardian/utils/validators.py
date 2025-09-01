import re

def normalize_phone(raw: str) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)

    # اگر با 00 شروع شد → جایگزین با +
    if digits.startswith("00"):
        digits = digits[2:]

    # اگر با 0 شروع شد (مثلاً 09...) → تبدیل به 98...
    if digits.startswith("0"):
        digits = "98" + digits[1:]

    # در نهایت باید با 98 شروع کنه
    if not digits.startswith("98"):
        return None

    return "+" + digits
