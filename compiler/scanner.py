from compiler.grammar import (
    KEYWORDS, OPERATORS, DELIMITERS,
    TOKEN_TYPES, DELIMITER_MAP,
)


class Token:
    """Одна распознанная лексема."""

    def __init__(self, code, type_name, lexeme, line, start, end):
        self.code = code
        self.type = type_name
        self.lexeme = lexeme
        self.line = line
        self.start = start
        self.end = end

    def __repr__(self):
        return f"Token({self.type}, '{self.lexeme}', line={self.line}, pos={self.start}-{self.end})"


class LexicalError:
    """Одна лексическая ошибка."""

    def __init__(self, message, line, col, character):
        self.message = message
        self.line = line
        self.col = col
        self.character = character

    def __repr__(self):
        return f"Ошибка: строка {self.line}, позиция {self.col}: {self.message} ('{self.character}')"


class Scanner:
    """Лексический анализатор для варианта 'Объявление структуры на языке Java'."""

    def __init__(self):
        self.tokens = []
        self.errors = []

    def scan(self, text):
        """Главный метод. Принимает текст, возвращает (tokens, errors)."""
        self.tokens = []
        self.errors = []
        lines = text.split("\n")
        for line_num, line in enumerate(lines, start=1):
            self._scan_line(line, line_num)
        return self.tokens, self.errors

    def _scan_line(self, line, line_num):
        """Пошагово обрабатывает одну строку."""
        i = 0
        length = len(line)
        buffer = []
        start_col = 0
        state = "START"

        while i < length:
            ch = line[i]
            col = i + 1

            if state == "START":
                start_col = col

                if ch.isalpha() or ch == "_":
                    state = "IDENT"
                    buffer.append(ch)
                    i += 1
                elif ch.isdigit():
                    state = "INTEGER"
                    buffer.append(ch)
                    i += 1
                elif ch == ".":
                    state = "FLOAT"
                    buffer.append(ch)
                    i += 1
                elif ch == '"':
                    state = "STRING"
                    buffer.append(ch)
                    i += 1
                elif ch == "'":
                    state = "CHAR"
                    buffer.append(ch)
                    i += 1
                elif ch.isspace():
                    state = "WHITESPACE"
                    buffer.append(ch)
                    i += 1
                elif ch in OPERATORS:
                    state = "OPERATOR"
                    buffer.append(ch)
                    i += 1
                elif ch in DELIMITERS:
                    self._emit_delimiter(ch, line_num, col)
                    i += 1
                else:
                    self._emit("UNKNOWN", ch, line_num, col, col)
                    i += 1

            elif state == "IDENT":
                if ch.isalnum() or ch == "_":
                    buffer.append(ch)
                    i += 1
                else:
                    lexeme = "".join(buffer)
                    token_type = "KEYWORD" if lexeme in KEYWORDS else "IDENTIFIER"
                    self._emit(token_type, lexeme, line_num, start_col, col - 1)
                    state = "START"
                    buffer = []

            elif state == "INTEGER":
                if ch.isdigit():
                    buffer.append(ch)
                    i += 1
                elif ch == ".":
                    buffer.append(ch)
                    state = "FLOAT"
                    i += 1
                else:
                    lexeme = "".join(buffer)
                    self._emit("INTEGER", lexeme, line_num, start_col, col - 1)
                    state = "START"
                    buffer = []

            elif state == "FLOAT":
                if ch.isdigit():
                    buffer.append(ch)
                    i += 1
                else:
                    lexeme = "".join(buffer)
                    self._emit("FLOAT", lexeme, line_num, start_col, col - 1)
                    state = "START"
                    buffer = []

            elif state == "STRING":
                buffer.append(ch)
                i += 1
                if ch == '"' and len(buffer) > 1:
                    lexeme = "".join(buffer)
                    self._emit("STRING", lexeme, line_num, start_col, col)
                    state = "START"
                    buffer = []

            elif state == "CHAR":
                buffer.append(ch)
                i += 1
                if ch == "'" and len(buffer) > 1:
                    lexeme = "".join(buffer)
                    self._emit("CHAR", lexeme, line_num, start_col, col)
                    state = "START"
                    buffer = []

            elif state == "WHITESPACE":
                if ch.isspace():
                    buffer.append(ch)
                    i += 1
                else:
                    lexeme = "".join(buffer)
                    self._emit("WHITESPACE", lexeme, line_num, start_col, col - 1)
                    state = "START"
                    buffer = []

            elif state == "OPERATOR":
                current = "".join(buffer)
                if ch in OPERATORS and (current + ch) in OPERATORS and len(current) == 1:
                    buffer.append(ch)
                    i += 1
                else:
                    lexeme = "".join(buffer)
                    self._emit("OPERATOR", lexeme, line_num, start_col, col - 1)
                    state = "START"
                    buffer = []

        if buffer:
            lexeme = "".join(buffer)
            end_col = start_col + len(lexeme) - 1
            if state == "IDENT":
                token_type = "KEYWORD" if lexeme in KEYWORDS else "IDENTIFIER"
                self._emit(token_type, lexeme, line_num, start_col, end_col)
            elif state in ("INTEGER", "FLOAT"):
                self._emit(state, lexeme, line_num, start_col, end_col)
            elif state == "WHITESPACE":
                self._emit("WHITESPACE", lexeme, line_num, start_col, end_col)
            elif state == "OPERATOR":
                self._emit("OPERATOR", lexeme, line_num, start_col, end_col)
            elif state in ("STRING", "CHAR"):
                self._emit("UNKNOWN", lexeme, line_num, start_col, end_col)

    def _emit(self, token_type, lexeme, line, start, end):
        """Добавить лексему в список или ошибку, если тип UNKNOWN."""
        if token_type == "UNKNOWN":
            self.errors.append(LexicalError("Недопустимый или незавершённый символ", line, start, lexeme))
            code = TOKEN_TYPES["UNKNOWN"]
        else:
            code = TOKEN_TYPES[token_type]
        self.tokens.append(Token(code, token_type, lexeme, line, start, end))

    def _emit_delimiter(self, ch, line, col):
        """Разделитель — отдельный код в зависимости от символа."""
        token_type = DELIMITER_MAP.get(ch, "UNKNOWN")
        code = TOKEN_TYPES[token_type]
        self.tokens.append(Token(code, token_type, ch, line, col, col))

    def get_tokens_table_data(self):
        """Данные для таблицы результатов: список строк."""
        data = []
        for t in self.tokens:
            if t.type == "UNKNOWN":
                continue
            data.append([
                t.code,
                t.type,
                t.lexeme,
                f"строка {t.line}, [{t.start}:{t.end}]",
            ])
        for e in self.errors:
            data.append([
                99,
                "ОШИБКА",
                e.character,
                f"строка {e.line}, [{e.col}:{e.col}]",
            ])
        return data