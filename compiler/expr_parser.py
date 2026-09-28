from compiler.grammar import OPERATORS


BINARY_OPS = {"+", "-", "*", "/", "%"}


class Quadruple:
    def __init__(self, op, arg1, arg2, result):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
        self.has_errors = False

    def __repr__(self):
        return f"({self.op}, {self.arg1}, {self.arg2}, {self.result})"


class ExprError:
    def __init__(self, message, line, col):
        self.message = message
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Ошибка: строка {self.line}, позиция {self.col}: {self.message}"


class ExprParser:
    def __init__(self):
        self.tokens = []
        self.pos = 0
        self.errors = []
        self.quads = []
        self.temp_count = 0

    def parse(self, tokens):
        self.tokens = [t for t in tokens if t.type in ("INTEGER", "IDENTIFIER", "OPERATOR", "LPAREN", "RPAREN")]
        self.pos = 0
        self.errors = []
        self.quads = []
        self.temp_count = 0
        self.has_errors = False

        if not self.tokens:
            self._add_error("Пустое выражение", 1, 1)
            return self.errors, self.quads, None

        self.parse_expr()

        if self.pos < len(self.tokens):
            tok = self.tokens[self.pos]
            self._add_error(f"Лишний токен '{tok.lexeme}' после выражения", tok.line, tok.start)

        if self.has_errors:
            self.quads = []

        return self.errors, self.quads, None

    def parse_expr(self):
        left = self.parse_term()
        return self.parse_expr_tail(left)

    def parse_expr_tail(self, left):
        while self._current() is not None and self._current().lexeme in ("+", "-"):
            op = self._current().lexeme
            self._advance()
            right = self.parse_term()
            t = self._new_temp()
            self._emit(op, left, right, t)
            left = t
        return left

    def parse_term(self):
        left = self.parse_factor()
        return self.parse_term_tail(left)

    def parse_term_tail(self, left):
        while self._current() is not None and self._current().lexeme in ("*", "/", "%"):
            op = self._current().lexeme
            self._advance()
            right = self.parse_factor()
            t = self._new_temp()
            self._emit(op, left, right, t)
            left = t
        return left

    def parse_factor(self):
        cur = self._current()
        if cur is None:
            self._add_error("Ожидался операнд, получен конец выражения", 0, 0)
            return "?"

        if cur.type == "INTEGER":
            self._advance()
            return cur.lexeme

        if cur.type == "IDENTIFIER":
            self._advance()
            return cur.lexeme

        if cur.type == "LPAREN":
            self._advance()
            inner = self.parse_expr()
            if self._current() is None or self._current().type != "RPAREN":
                self._add_error("Ожидалась закрывающая скобка ')'", cur.line, cur.start)
                return inner
            self._advance()
            return inner

        self._add_error(f"Ожидался операнд, получено '{cur.lexeme}'", cur.line, cur.start)
        self._advance()
        return "?"

    def _current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _advance(self):
        if self.pos < len(self.tokens):
            self.pos += 1

    def _new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def _emit(self, op, arg1, arg2, result):
        self.quads.append(Quadruple(op, arg1, arg2, result))

    def _add_error(self, message, line, col):
        self.errors.append(ExprError(message, line, col))
        self.has_errors = True

def to_polish(tokens):
    filtered = [t for t in tokens if t.type in ("INTEGER", "IDENTIFIER", "OPERATOR", "LPAREN", "RPAREN")]

    precedence = {"+": 1, "-": 1, "*": 2, "/": 2, "%": 2}
    output = []
    stack = []

    for tok in filtered:
        if tok.type in ("INTEGER", "IDENTIFIER"):
            output.append(tok.lexeme)
        elif tok.lexeme == "(":
            stack.append(tok.lexeme)
        elif tok.lexeme == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if stack and stack[-1] == "(":
                stack.pop()
        elif tok.lexeme in BINARY_OPS:
            while stack and stack[-1] != "(" and precedence.get(stack[-1], 0) >= precedence[tok.lexeme]:
                output.append(stack.pop())
            stack.append(tok.lexeme)

    while stack:
        output.append(stack.pop())

    return output


def evaluate_polish(polish):
    stack = []

    for token in polish:
        if token in BINARY_OPS:
            if len(stack) < 2:
                return None, "Недостаточно операндов"
            b = stack.pop()
            a = stack.pop()
            if not (isinstance(a, int) and isinstance(b, int)):
                return None, "Присутствуют идентификаторы"
            if token == "+":
                stack.append(a + b)
            elif token == "-":
                stack.append(a - b)
            elif token == "*":
                stack.append(a * b)
            elif token == "/":
                if b == 0:
                    return None, "Деление на ноль"
                stack.append(a // b)
            elif token == "%":
                if b == 0:
                    return None, "Деление на ноль"
                stack.append(a % b)
        else:
            try:
                stack.append(int(token))
            except ValueError:
                return None, "Присутствуют идентификаторы"

    if len(stack) != 1:
        return None, "Некорректное выражение"

    return stack[0], None