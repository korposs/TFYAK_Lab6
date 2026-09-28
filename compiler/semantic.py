ALLOWED_TYPES = {"String", "int", "long", "double", "float", "boolean", "char", "byte", "short"}
MAX_PARAMS = 255


class SemanticError:
    def __init__(self, kind, message, line, col):
        self.kind = kind
        self.message = message
        self.line = line
        self.col = col

    @property
    def position(self):
        return f"Строка {self.line}, позиция {self.col}"

    def __repr__(self):
        return f"SemanticError({self.kind}, '{self.message}', {self.position})"


class Symbol:
    def __init__(self, name, type_, line, col):
        self.name = name
        self.type = type_
        self.line = line
        self.col = col


class SymbolTable:
    def __init__(self, parent=None):
        self.parent = parent
        self.symbols = {}

    def check_duplicate(self, name):
        return name in self.symbols

    def declare(self, name, type_, line, col):
        """Возвращает None при успехе, иначе - предыдущий Symbol."""
        if self.check_duplicate(name):
            return self.symbols[name]
        self.symbols[name] = Symbol(name, type_, line, col)
        return None

    def lookup(self, name):
        table = self
        while table is not None:
            if name in table.symbols:
                return table.symbols[name]
            table = table.parent
        return None


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.global_scope = SymbolTable()

    def analyze(self, root):
        self.errors = []
        self.global_scope = SymbolTable()
        for record in root.children:
            self._record(record)
        return self.errors

    def _error(self, kind, message, line, col):
        self.errors.append(SemanticError(kind, message, line, col))

    def _record(self, record):
        attrs = record.attributes
        prev = self.global_scope.declare(attrs["name"], "record", attrs["line"], attrs["col"])
        if prev:
            self._error(
                "Повторное объявление",
                f'Идентификатор "{attrs["name"]}" уже объявлен в строке {prev.line}',
                attrs["line"],
                attrs["col"],
            )

        if len(record.children) > MAX_PARAMS:
            self._error(
                "Превышен лимит",
                f"Число параметров {len(record.children)} превышает {MAX_PARAMS}",
                attrs["line"],
                attrs["col"],
            )

        scope = SymbolTable(self.global_scope)
        for type_node in record.children:
            self._parameter(type_node, scope)

    def _parameter(self, type_node, scope):
        param = type_node.children[0]
        t = type_node.attributes
        p = param.attributes

        if t["name"] not in ALLOWED_TYPES:
            self._error("Неизвестный тип", f'Неизвестный тип "{t["name"]}"', t["line"], t["col"])

        prev = scope.declare(p["name"], t["name"], p["line"], p["col"])
        if prev:
            self._error(
                "Повтор параметра",
                f'Параметр "{p["name"]}" уже объявлен в этом record',
                p["line"],
                p["col"],
            )