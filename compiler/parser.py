from compiler.grammar import KEYWORDS


TYPE_KEYWORDS = {
    "String", "int", "long", "double", "float",
    "boolean", "char", "byte", "short",
}


class SyntaxError:
    def __init__(self, fragment, line, col, message):
        self.fragment = fragment
        self.line = line
        self.col = col
        self.message = message

    def __repr__(self):
        return f"Ошибка: строка {self.line}, позиция {self.col}: {self.message} ('{self.fragment}')"


class Parser:
    def __init__(self):
        self.tokens = []
        self.pos = 0
        self.errors = []

    def parse(self, tokens):
        self.tokens = [t for t in tokens if t.type != "WHITESPACE"]
        self.pos = 0
        self.errors = []

        self.parse_program()
        return self.errors

    def parse_program(self):
        safety = 0
        max_iterations = len(self.tokens) * 3 + 10

        while self._current() is not None:
            safety += 1
            if safety > max_iterations:
                break

            if not self._is_record(self._current()):
                tok = self._current()
                self._add_error(tok.lexeme, tok.line, tok.start,
                                "Ожидалось ключевое слово 'record'")
                self._skip_to_sync()
                continue

            pos_before = self.pos
            self.parse_declaration()

            if self.pos == pos_before:
                self._advance()

    def parse_declaration(self):
        if not self._expect_keyword("record", "Ожидалось ключевое слово 'record'"):
            self._skip_to_sync()
            return

        if not self._expect_type("IDENTIFIER", "Ожидался идентификатор имени структуры"):
            self._skip_to_sync()
            return

        if not self._expect_type("LPAREN", "Ожидалась открывающая скобка '('"):
            self._skip_to_sync()
            return

        if not self.parse_param_list():
            self._skip_to_sync()
            return

        if not self._expect_type("RPAREN", "Ожидалась закрывающая скобка ')'"):
            self._skip_to_sync()
            return

        if not self._expect_type("LBRACE", "Ожидалась открывающая фигурная скобка '{'"):
            self._skip_to_sync()
            return

        if not self._expect_type("RBRACE", "Ожидалась закрывающая фигурная скобка '}'"):
            self._skip_to_sync()
            return

        if not self._expect_type("SEMICOLON", "Ожидалась точка с запятой ';'"):
            self._skip_to_sync()
            return

    def parse_param_list(self):
        cur = self._current()
        if cur is None:
            return True

        if cur.type == "RPAREN":
            return True

        if not self.parse_param():
            return False

        return self.parse_tail()

    def parse_param(self):
        if not self.parse_type():
            return False

        if not self._expect_type("IDENTIFIER", "Ожидался идентификатор параметра"):
            return False

        return True

    def parse_type(self):
        """Type -> String | int | ... | id"""
        cur = self._current()
        if cur is None:
            self._add_error("EOF", 0, 0, "Ожидался тип параметра")
            return False

        if cur.type == "KEYWORD" and cur.lexeme in TYPE_KEYWORDS:
            self._advance()
            return True

        if cur.type == "IDENTIFIER":
            self._advance()
            return True

        self._add_error(cur.lexeme, cur.line, cur.start, f"Ожидался тип параметра, получено '{cur.lexeme}'")
        return False

    def parse_tail(self):
        cur = self._current()
        if cur is None:
            return True

        if cur.type == "COMMA":
            self._advance()
            if not self.parse_param():
                return False
            return self.parse_tail()

        return True

    def _current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _advance(self):
        if self.pos < len(self.tokens):
            self.pos += 1

    def _is_record(self, token):
        if token is None:
            return False
        return token.type == "KEYWORD" and token.lexeme == "record"

    def _expect_keyword(self, keyword, message):
        cur = self._current()
        if cur is not None and cur.type == "KEYWORD" and cur.lexeme == keyword:
            self._advance()
            return True
        if cur is not None:
            self._add_error(cur.lexeme, cur.line, cur.start, message)
        else:
            self._add_error("EOF", 0, 0, message)
        return False

    def _expect_type(self, token_type, message):
        cur = self._current()
        if cur is not None and cur.type == token_type:
            self._advance()
            return True
        if cur is not None:
            self._add_error(cur.lexeme, cur.line, cur.start, message)
        else:
            self._add_error("EOF", 0, 0, message)
        return False

    def _skip_to_sync(self):
        while self._current() is not None:
            cur = self._current()
            if cur.type == "SEMICOLON":
                self._advance()
                return
            if cur.type == "KEYWORD" and cur.lexeme == "record":
                return
            self._advance()

    def _add_error(self, fragment, line, col, message):
        self.errors.append(SyntaxError(fragment, line, col, message))