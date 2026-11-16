import re

_NUMBER_RE = re.compile(r"\(?-?\d[\d,]*\.?\d*\)?%?")

_SCALES = (1, 1e3, 1e5, 1e6, 1e7)


def extract_numbers(text: str) -> list[float]:
    numbers = []
    for match in _NUMBER_RE.findall(text or ""):
        cleaned = match.strip()
        is_negative = cleaned.startswith("(") and cleaned.endswith(")")
        cleaned = cleaned.strip("()%").replace(",", "")
        if not cleaned or cleaned == "-":
            continue
        try:
            value = float(cleaned)
        except ValueError:
            continue
        numbers.append(-value if is_negative else value)
    return numbers


def number_present(claimed_value: float, source_text: str, rel_tolerance: float = 0.01) -> bool:
    if claimed_value == 0:
        return True

    candidates = extract_numbers(source_text)
    if not candidates:
        return False

    for scale in _SCALES:
        target = claimed_value / scale
        for candidate in candidates:
            if candidate == 0:
                continue
            if abs(candidate - target) <= abs(target) * rel_tolerance:
                return True
    return False
