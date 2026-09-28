# Константы грамматики языка Java для варианта. Объявление структуры на языке Java


# Ключевые слова
KEYWORDS = {
    "record",
    "String",
    "int",
    "long",
    "double",
    "float",
    "boolean",
    "char",
    "byte",
    "short",
}

# Операторы (от длинных к коротким — важно для корректного распознавания)
OPERATORS = {
    "==", "!=", "<=", ">=", "&&", "||",
    "=", "<", ">", "+", "-", "*", "/", "!",
}

# Разделители
DELIMITERS = {
    "(", ")", "{", "}", "[", "]",
    ",", ";", ".",
}

# Числовые коды типов лексем
TOKEN_TYPES = {
    "KEYWORD":     1,
    "IDENTIFIER":  2,
    "INTEGER":     3,
    "FLOAT":       4,
    "STRING":      5,
    "CHAR":        6,
    "OPERATOR":    7,
    "LPAREN":      8,    # (
    "RPAREN":      9,    # )
    "LBRACE":     10,    # {
    "RBRACE":     11,    # }
    "COMMA":      12,    # ,
    "SEMICOLON":  13,    # ;
    "WHITESPACE": 14,
    "UNKNOWN":    99,
}

# Соответствие конкретных разделителей их типам
DELIMITER_MAP = {
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    ",": "COMMA",
    ";": "SEMICOLON",
}