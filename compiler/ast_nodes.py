import json


class AstNode:
    def __init__(self, **attributes):
        self.children = []
        self.attributes = attributes

    @property
    def kind(self):
        return type(self).__name__

    def add(self, child):
        self.children.append(child)
        return child

    def label(self):
        if not self.attributes:
            return self.kind
        parts = []
        for key, value in self.attributes.items():
            shown = f'"{value}"' if isinstance(value, str) else value
            parts.append(f"{key}: {shown}")
        return f"{self.kind} ({', '.join(parts)})"

    def to_dict(self):
        return {
            "node": self.kind,
            "attributes": self.attributes,
            "children": [c.to_dict() for c in self.children],
        }

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_tree(self):
        lines = [self.label()]
        self._walk(lines, "")
        return "\n".join(lines)

    def _walk(self, lines, prefix):
        for i, child in enumerate(self.children):
            last = i == len(self.children) - 1
            lines.append(prefix + ("└── " if last else "├── ") + child.label())
            child._walk(lines, prefix + ("    " if last else "│   "))


class ProgramNode(AstNode):
    pass


class RecordDeclNode(AstNode):
    pass


class TypeNode(AstNode):
    pass


class ParameterNode(AstNode):
    pass


class AstBuilder:
    def build(self, tokens):
        items = [t for t in tokens if t.type != "WHITESPACE"]
        root = ProgramNode()
        i = 0
        while i < len(items):
            i = self._record(items, i, root)
        return root

    def _record(self, items, i, root):
        # items[i] — 'record'
        i += 1
        name_token = items[i]
        record = root.add(RecordDeclNode(name=name_token.lexeme, line=name_token.line, col=name_token.start))
        i += 1

        # items[i] — '('
        i += 1

        while items[i].type != "RPAREN":
            type_token = items[i]
            i += 1
            id_token = items[i]
            i += 1

            type_node = record.add(TypeNode(name=type_token.lexeme, line=type_token.line, col=type_token.start))
            type_node.add(ParameterNode(name=id_token.lexeme, line=id_token.line, col=id_token.start))

            if items[i].type == "COMMA":
                i += 1

        # items[i] — ')'
        i += 1
        # items[i] — '{'
        i += 1
        # items[i] — '}'
        i += 1
        # items[i] — ';'
        i += 1

        return i