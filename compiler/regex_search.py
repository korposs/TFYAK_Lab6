import re
PATTERN_OGRN = r"\b[15](0[2-9]|1\d|2[0-6])(0[1-9]|[1-7]\d|8[0-9])\d{8}\b"

PATTERN_PASCAL_COMMENT = r"\{[^}]*\}|\(\*.*?\*\)"

RGB_NUMBER = r"(25[0-5]|2[0-4]\d|1\d\d|\d\d?)"
PATTERN_RGB = r"rgb\(\s*" + RGB_NUMBER + r"\s*,\s*" + RGB_NUMBER + r"\s*,\s*" + RGB_NUMBER + r"\s*\)"

SEARCH_TASKS = [
    ("ОГРН юридического лица", PATTERN_OGRN),
    ("Комментарии Pascal", PATTERN_PASCAL_COMMENT),
    ("RGB-цвет", PATTERN_RGB),
]

class Match:
    def __init__(self, text, line, start_col, length):
        self.text = text
        self.line = line
        self.start = start_col
        self.length = length

    def __repr__(self):
        return f"Match('{self.text}', line={self.line}, pos={self.start}, len={self.length})"


def _line_col_from_pos(text, pos):
    line = text.count("\n", 0, pos) + 1
    line_start = text.rfind("\n", 0, pos) + 1
    col = pos - line_start + 1
    return line, col


def _is_valid_ogrn(ogrn):
    first12 = int(ogrn[:12])
    control = first12 % 11
    if control == 10:
        control = 0
    return control == int(ogrn[12])


def search(text, pattern):
    if not text.strip():
        return []

    results = []
    for m in re.finditer(pattern, text, re.MULTILINE):
        matched_text = m.group(0)

        if pattern == PATTERN_OGRN and not _is_valid_ogrn(matched_text):
            continue

        line, col = _line_col_from_pos(text, m.start())
        results.append(Match(matched_text, line, col, len(matched_text)))
    return results