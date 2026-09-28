import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPalette, QColor, QBrush
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox, QPlainTextEdit, QSplitter, QStyleFactory, QToolBar, QTableWidget, QTableWidgetItem, QComboBox, QLabel, QTabWidget

from compiler.scanner import Scanner
from compiler.parser import Parser
from compiler.ast_nodes import AstBuilder
from compiler.semantic import SemanticAnalyzer
from compiler.regex_search import search as regex_search, SEARCH_TASKS
from compiler.expr_parser import ExprParser, to_polish, evaluate_polish

APP_TITLE = "Текстовый редактор"
ICONS_DIR = Path(__file__).parent / "resources" / "icons"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_file = None
        self.current_mode = None

        self.setWindowTitle(APP_TITLE)
        self.resize(1000, 700)

        self._create_editor_area()
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._connect_actions()

    def _create_editor_area(self):
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Введите исходный текст...")

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["Код", "Тип", "Лексема", "Местоположение"])
        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.itemClicked.connect(self._on_table_clicked)
        self.result_table.setColumnWidth(0, 220)
        self.result_table.setColumnWidth(1, 200)
        self.result_table.setColumnWidth(2, 100)

        self.ast_tree_view = QPlainTextEdit()
        self.ast_tree_view.setReadOnly(True)
        self.ast_tree_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.ast_json_view = QPlainTextEdit()
        self.ast_json_view.setReadOnly(True)
        self.ast_json_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.quads_view = QPlainTextEdit()
        self.quads_view.setReadOnly(True)
        self.quads_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.polish_view = QPlainTextEdit()
        self.polish_view.setReadOnly(True)
        self.polish_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.result_view = QPlainTextEdit()
        self.result_view.setReadOnly(True)
        self.result_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.ast_tabs = QTabWidget()
        self.ast_tabs.addTab(self.ast_tree_view, "Дерево AST")
        self.ast_tabs.addTab(self.ast_json_view, "JSON")
        self.ast_tabs.addTab(self.quads_view, "Тетрады")
        self.ast_tabs.addTab(self.polish_view, "ПОЛИЗ")
        self.ast_tabs.addTab(self.result_view, "Результат")

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.result_table)
        splitter.addWidget(self.ast_tabs)
        splitter.setSizes([300, 200, 250])
        splitter.setChildrenCollapsible(False)

        self.setCentralWidget(splitter)

    def _create_actions(self):
        self.new_action = QAction("Создать", self)
        self.open_action = QAction("Открыть", self)
        self.save_action = QAction("Сохранить", self)
        self.save_as_action = QAction("Сохранить как", self)
        self.exit_action = QAction("Выход", self)

        self.undo_action = QAction("Отменить", self)
        self.redo_action = QAction("Повторить", self)
        self.cut_action = QAction("Вырезать", self)
        self.copy_action = QAction("Копировать", self)
        self.paste_action = QAction("Вставить", self)
        self.delete_action = QAction("Удалить", self)
        self.select_all_action = QAction("Выделить всё", self)

        self.task_action = QAction("Постановка задачи", self)
        self.grammar_action = QAction("Грамматика", self)
        self.classification_action = QAction("Классификация грамматики", self)
        self.method_action = QAction("Метод анализа", self)
        self.example_action = QAction("Тестовый пример", self)
        self.literature_action = QAction("Список литературы", self)
        self.source_action = QAction("Исходный код программы", self)

        self.run_lexer_action = QAction("Лексический анализ", self)
        self.run_parser_action = QAction("Синтаксический анализ", self)
        self.run_regex_action = QAction("Поиск подстрок", self)
        self.run_semantic_action = QAction("Семантический анализ и AST", self)
        self.run_vpp_action = QAction("Внутренняя форма программы", self)

        self.help_action = QAction("Вызов справки", self)
        self.about_action = QAction("О программе", self)

        self._setup_shortcuts()
        self._setup_icons()

    def _setup_shortcuts(self):
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.exit_action.setShortcut(QKeySequence("Alt+F4"))

        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.delete_action.setShortcut(QKeySequence("Delete"))
        self.select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)

        self.run_lexer_action.setShortcut(QKeySequence("F5"))
        self.run_parser_action.setShortcut(QKeySequence("F6"))
        self.run_regex_action.setShortcut(QKeySequence("F7"))
        self.run_semantic_action.setShortcut(QKeySequence("F8"))
        self.run_vpp_action.setShortcut(QKeySequence("F9"))

        self.help_action.setShortcut(QKeySequence.StandardKey.HelpContents)

    def _setup_icons(self):
        icon_map = {
            self.new_action: "new.png",
            self.open_action: "open.png",
            self.save_action: "save.png",
            self.undo_action: "undo.png",
            self.redo_action: "redo.png",
            self.cut_action: "cut.png",
            self.copy_action: "copy.png",
            self.paste_action: "paste.png",
            self.delete_action: "delete.png",
            self.help_action: "help.png",
            self.about_action: "about.png",
            self.run_lexer_action: "run_lex.png",
            self.run_parser_action: "run_synt.png",
            self.run_regex_action: "run.png",
            self.run_semantic_action: "run_sem.png",
            self.run_vpp_action: "run.png",
        }

        for action, filename in icon_map.items():
            path = ICONS_DIR / filename
            if path.exists():
                action.setIcon(QIcon(str(path)))
            else:
                print(f"[WARN] Иконка не найдена: {path}", file=sys.stderr)
            action.setIconVisibleInMenu(False)

    def _create_menus(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("Файл")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu = menu_bar.addMenu("Правка")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.cut_action)
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addAction(self.delete_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.select_all_action)

        text_menu = menu_bar.addMenu("Текст")
        text_menu.addAction(self.task_action)
        text_menu.addAction(self.grammar_action)
        text_menu.addAction(self.classification_action)
        text_menu.addAction(self.method_action)
        text_menu.addAction(self.example_action)
        text_menu.addAction(self.literature_action)
        text_menu.addAction(self.source_action)

        run_menu = menu_bar.addMenu("Пуск")
        run_menu.addAction(self.run_lexer_action)
        run_menu.addAction(self.run_parser_action)
        run_menu.addAction(self.run_semantic_action)
        run_menu.addSeparator()
        run_menu.addAction(self.run_vpp_action)
        run_menu.addAction(self.run_regex_action)

        help_menu = menu_bar.addMenu("Справка")
        help_menu.addAction(self.help_action)
        help_menu.addAction(self.about_action)

    def _create_toolbar(self):
        toolbar = QToolBar("Панель инструментов", self)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()
        toolbar.addAction(self.cut_action)
        toolbar.addAction(self.copy_action)
        toolbar.addAction(self.paste_action)
        toolbar.addAction(self.delete_action)
        toolbar.addSeparator()
        toolbar.addAction(self.run_lexer_action)
        toolbar.addAction(self.run_parser_action)
        toolbar.addAction(self.run_semantic_action)
        toolbar.addAction(self.run_vpp_action)
        toolbar.addSeparator()
        toolbar.addAction(self.help_action)
        toolbar.addAction(self.about_action)

        toolbar.addSeparator()

        toolbar.addWidget(QLabel("  Тип поиска: "))

        self.search_combo = QComboBox()
        for name, _ in SEARCH_TASKS:
            self.search_combo.addItem(name)
        self.search_combo.setMinimumWidth(220)
        toolbar.addWidget(self.search_combo)

        toolbar.addSeparator()
        toolbar.addAction(self.run_regex_action)

        self.addToolBar(toolbar)

    def _connect_actions(self):
        self.new_action.triggered.connect(self._on_new)
        self.open_action.triggered.connect(self._on_open)
        self.save_action.triggered.connect(self._on_save)
        self.save_as_action.triggered.connect(self._on_save_as)
        self.exit_action.triggered.connect(self.close)

        self.undo_action.triggered.connect(self.editor.undo)
        self.redo_action.triggered.connect(self.editor.redo)
        self.cut_action.triggered.connect(self.editor.cut)
        self.copy_action.triggered.connect(self.editor.copy)
        self.paste_action.triggered.connect(self.editor.paste)
        self.delete_action.triggered.connect(self._on_delete_selection)
        self.select_all_action.triggered.connect(self.editor.selectAll)

        self.task_action.triggered.connect(lambda: self._on_show_text_info("Постановка задачи", "Здесь будет постановка задачи."))
        self.grammar_action.triggered.connect(lambda: self._on_show_text_info("Грамматика", "Здесь будет описание грамматики."))
        self.classification_action.triggered.connect(lambda: self._on_show_text_info("Классификация грамматики", "Здесь будет классификация грамматики."))
        self.method_action.triggered.connect(lambda: self._on_show_text_info("Метод анализа", "Здесь будет описание метода анализа."))
        self.example_action.triggered.connect(lambda: self._on_show_text_info("Тестовый пример", "Здесь будет тестовый пример."))
        self.literature_action.triggered.connect(lambda: self._on_show_text_info("Список литературы", "Здесь будет список литературы."))
        self.source_action.triggered.connect(lambda: self._on_show_text_info("Исходный код программы", "Здесь будет информация об исходном коде."))

        self.run_lexer_action.triggered.connect(self._on_run_lexer)
        self.run_parser_action.triggered.connect(self._on_run_parser)
        self.run_regex_action.triggered.connect(self._on_run_regex)
        self.run_semantic_action.triggered.connect(self._on_run_semantic)
        self.run_vpp_action.triggered.connect(self._on_run_vpp)

        self.help_action.triggered.connect(self._on_show_help)
        self.about_action.triggered.connect(self._on_show_about)

    def _on_delete_selection(self):
        cursor = self.editor.textCursor()
        cursor.removeSelectedText()
        self.editor.setTextCursor(cursor)

    def _on_new(self):
        if not self._maybe_save():
            return
        self.editor.clear()
        self.current_file = None
        self._update_title()

    def _on_open(self):
        if not self._maybe_save():
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "Текстовые файлы (*.txt);;Все файлы (*.*)")
        if not file_path:
            return

        try:
            text = Path(file_path).read_text(encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{exc}")
            return

        self.editor.setPlainText(text)
        self.editor.document().setModified(False)
        self.current_file = file_path
        self._update_title()

    def _on_save(self):
        if self.current_file is None:
            return self._on_save_as()

        try:
            Path(self.current_file).write_text(self.editor.toPlainText(), encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{exc}")
            return False

        self.editor.document().setModified(False)
        self._update_title()
        return True

    def _on_save_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", self.current_file or "", "Текстовые файлы (*.txt);;Все файлы (*.*)")
        if not file_path:
            return False

        self.current_file = file_path
        return self._on_save()

    def _maybe_save(self):
        if not self.editor.document().isModified():
            return True

        result = QMessageBox.question(self, "Сохранение изменений", "Сохранить изменения в текущем документе?", QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)

        if result == QMessageBox.StandardButton.Save:
            return self._on_save()
        if result == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def _update_title(self):
        if self.current_file:
            self.setWindowTitle(f"{APP_TITLE} - {self.current_file}")
        else:
            self.setWindowTitle(APP_TITLE)

    def _on_run_lexer(self):
        self.current_mode = "lexer"
        text = self.editor.toPlainText()
        scanner = Scanner()
        tokens, errors = scanner.scan(text)

        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["Код", "Тип", "Лексема", "Местоположение"])
        self.result_table.setRowCount(0)

        for token in tokens:
            if token.type == "UNKNOWN":
                continue
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(str(token.code)))
            self.result_table.setItem(row, 1, QTableWidgetItem(token.type))
            self.result_table.setItem(row, 2, QTableWidgetItem(self._display_lexeme(token)))
            self.result_table.setItem(row, 3, QTableWidgetItem(f"Строка {token.line}, позиция {token.start}"))

        red_bg = QColor(255, 220, 220)
        red_fg = QColor(180, 0, 0)

        for error in errors:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            code_item = QTableWidgetItem("99")
            type_item = QTableWidgetItem("ОШИБКА")
            lexeme = error.character
            if lexeme.isspace():
                lexeme = "(пробел)" if lexeme == " " else "(пробелы)"
            lexeme_item = QTableWidgetItem(lexeme)
            location_item = QTableWidgetItem(f"Строка {error.line}, позиция {error.col}")
            for item in (code_item, type_item, lexeme_item, location_item):
                item.setBackground(QBrush(red_bg))
                item.setForeground(QBrush(red_fg))
            self.result_table.setItem(row, 0, code_item)
            self.result_table.setItem(row, 1, type_item)
            self.result_table.setItem(row, 2, lexeme_item)
            self.result_table.setItem(row, 3, location_item)

        total_lexemes = len([t for t in tokens if t.type != "UNKNOWN"])
        total_errors = len(errors)
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)
        summary = QTableWidgetItem(f"Итого: лексем - {total_lexemes}, ошибок - {total_errors}")
        font = summary.font()
        font.setBold(True)
        summary.setFont(font)
        summary.setBackground(QBrush(QColor(230, 230, 230)))
        self.result_table.setItem(row, 0, summary)
        self.result_table.setSpan(row, 0, 1, 4)

        self.statusBar().showMessage(f"Лексем: {total_lexemes}, ошибок: {total_errors}")

    def _on_run_parser(self):
        self.current_mode = "parser"
        text = self.editor.toPlainText()
        scanner = Scanner()
        tokens, _ = scanner.scan(text)

        parser = Parser()
        syntax_errors = parser.parse(tokens)

        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["Неверный фрагмент", "Местоположение", "Описание ошибки"])
        self.result_table.setRowCount(0)

        red_bg = QColor(255, 220, 220)
        red_fg = QColor(180, 0, 0)

        for err in syntax_errors:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            fragment_item = QTableWidgetItem(err.fragment)
            location_item = QTableWidgetItem(f"Строка {err.line}, позиция {err.col}")
            message_item = QTableWidgetItem(err.message)
            for item in (fragment_item, location_item, message_item):
                item.setBackground(QBrush(red_bg))
                item.setForeground(QBrush(red_fg))
            self.result_table.setItem(row, 0, fragment_item)
            self.result_table.setItem(row, 1, location_item)
            self.result_table.setItem(row, 2, message_item)

        total_errors = len(syntax_errors)
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)
        if total_errors == 0:
            summary = QTableWidgetItem("Синтаксис корректен, ошибок нет")
        else:
            summary = QTableWidgetItem(f"Итого: ошибок - {total_errors}")
        font = summary.font()
        font.setBold(True)
        summary.setFont(font)
        summary.setBackground(QBrush(QColor(230, 230, 230)))
        self.result_table.setItem(row, 0, summary)
        self.result_table.setSpan(row, 0, 1, 3)

        self.statusBar().showMessage(f"Синтаксических ошибок: {total_errors}")

    def _on_run_regex(self):
        self.current_mode = "regex"
        text = self.editor.toPlainText()

        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["Найденная подстрока", "Начальная позиция", "Длина"])
        self.result_table.setRowCount(0)

        if not text.strip():
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            summary = QTableWidgetItem("Нет данных для поиска")
            font = summary.font()
            font.setBold(True)
            summary.setFont(font)
            summary.setBackground(QBrush(QColor(230, 230, 230)))
            self.result_table.setItem(row, 0, summary)
            self.result_table.setSpan(row, 0, 1, 3)
            self.statusBar().showMessage("Нет данных для поиска")
            return

        idx = self.search_combo.currentIndex()
        pattern = SEARCH_TASKS[idx][1]

        matches = regex_search(text, pattern)

        for m in matches:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(m.text))
            self.result_table.setItem(row, 1, QTableWidgetItem(f"Строка {m.line}, позиция {m.start}"))
            self.result_table.setItem(row, 2, QTableWidgetItem(str(m.length)))

        total = len(matches)
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)
        if total == 0:
            summary = QTableWidgetItem("Совпадений не найдено")
        else:
            summary = QTableWidgetItem(f"Итого найдено совпадений: {total}")
        font = summary.font()
        font.setBold(True)
        summary.setFont(font)
        summary.setBackground(QBrush(QColor(230, 230, 230)))
        self.result_table.setItem(row, 0, summary)
        self.result_table.setSpan(row, 0, 1, 3)

        self.statusBar().showMessage(f"Найдено совпадений: {total}")

    def _on_run_semantic(self):
        text = self.editor.toPlainText()

        scanner = Scanner()
        tokens, _ = scanner.scan(text)

        parser = Parser()
        syntax_errors = parser.parse(tokens)

        if syntax_errors:
            self.ast_tree_view.clear()
            self.ast_json_view.clear()
            self._on_run_parser()
            return

        self.current_mode = "semantic"

        builder = AstBuilder()
        root = builder.build(tokens)

        analyzer = SemanticAnalyzer()
        errors = analyzer.analyze(root)

        self._show_semantic_errors(errors)

        self.ast_tree_view.setPlainText(root.to_tree())
        self.ast_json_view.setPlainText(root.to_json())

    def _show_semantic_errors(self, errors):
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["Тип ошибки", "Сообщение", "Позиция"])
        self.result_table.setRowCount(0)

        red_bg = QColor(255, 220, 220)
        red_fg = QColor(180, 0, 0)

        for err in errors:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            kind_item = QTableWidgetItem(err.kind)
            message_item = QTableWidgetItem(err.message)
            pos_item = QTableWidgetItem(err.position)
            for item in (kind_item, message_item, pos_item):
                item.setBackground(QBrush(red_bg))
                item.setForeground(QBrush(red_fg))
            self.result_table.setItem(row, 0, kind_item)
            self.result_table.setItem(row, 1, message_item)
            self.result_table.setItem(row, 2, pos_item)

        total_errors = len(errors)
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)
        if total_errors == 0:
            summary = QTableWidgetItem("Семантических ошибок нет")
        else:
            summary = QTableWidgetItem(f"Итого: ошибок - {total_errors}")
        font = summary.font()
        font.setBold(True)
        summary.setFont(font)
        summary.setBackground(QBrush(QColor(230, 230, 230)))
        self.result_table.setItem(row, 0, summary)
        self.result_table.setSpan(row, 0, 1, 3)

        self.statusBar().showMessage(f"Семантических ошибок: {total_errors}")

    def _on_run_vpp(self):
        self.current_mode = "vpp"
        text = self.editor.toPlainText()

        scanner = Scanner()
        tokens, _ = scanner.scan(text)

        parser = ExprParser()
        errors, quads, _ = parser.parse(tokens)

        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["Тип ошибки", "Сообщение", "Позиция"])
        self.result_table.setRowCount(0)

        red_bg = QColor(255, 220, 220)
        red_fg = QColor(180, 0, 0)

        for err in errors:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            kind_item = QTableWidgetItem("Ошибка")
            message_item = QTableWidgetItem(err.message)
            pos_item = QTableWidgetItem(f"Строка {err.line}, позиция {err.col}")
            for item in (kind_item, message_item, pos_item):
                item.setBackground(QBrush(red_bg))
                item.setForeground(QBrush(red_fg))
            self.result_table.setItem(row, 0, kind_item)
            self.result_table.setItem(row, 1, message_item)
            self.result_table.setItem(row, 2, pos_item)

        total_errors = len(errors)
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)
        if total_errors == 0:
            summary = QTableWidgetItem("Ошибок нет")
        else:
            summary = QTableWidgetItem(f"Итого: ошибок - {total_errors}")
        font = summary.font()
        font.setBold(True)
        summary.setFont(font)
        summary.setBackground(QBrush(QColor(230, 230, 230)))
        self.result_table.setItem(row, 0, summary)
        self.result_table.setSpan(row, 0, 1, 3)

        self.statusBar().showMessage(f"Ошибок: {total_errors}")

        if errors:
            self.quads_view.setPlainText("Разбор не выполнен из-за ошибок")
            self.polish_view.setPlainText("Разбор не выполнен из-за ошибок")
            self.result_view.setPlainText("Разбор не выполнен из-за ошибок")
            return

        if not quads:
            self.quads_view.setPlainText("Тетрады отсутствуют")
            self.polish_view.setPlainText("ПОЛИЗ отсутствует")
            self.result_view.setPlainText("Нечего вычислять")
            return

        quads_text = "\n".join(
            f"{i + 1}. ({q.op}, {q.arg1}, {q.arg2}, {q.result})"
            for i, q in enumerate(quads)
        )
        self.quads_view.setPlainText(quads_text)

        polish = to_polish(tokens)
        self.polish_view.setPlainText(" ".join(polish))

        value, msg = evaluate_polish(polish)
        if value is not None:
            self.result_view.setPlainText(str(value))
        else:
            self.result_view.setPlainText(msg if msg else "Не вычислимо")

    def _display_lexeme(self, token):
        if token.type == "WHITESPACE":
            if "\t" in token.lexeme:
                return "(табуляция)"
            return "(пробел)"
        return token.lexeme

    def _on_table_clicked(self, item):
        row = item.row()

        if self.current_mode == "vpp":
            location_item = self.result_table.item(row, 2)
            if not location_item:
                return
            self._highlight_in_editor(location_item.text(), 1)
            return
        
        if self.current_mode == "semantic":
            location_item = self.result_table.item(row, 2)
            if not location_item:
                return
            self._highlight_in_editor(location_item.text(), 1)
            return

        if self.current_mode == "regex":
            location_item = self.result_table.item(row, 1)
            length_item = self.result_table.item(row, 2)
            if not location_item or not length_item:
                return
            try:
                length = int(length_item.text())
            except ValueError:
                return
            self._highlight_in_editor(location_item.text(), length)
            return

        if self.current_mode == "parser":
            location_item = self.result_table.item(row, 1)
            if not location_item:
                return
            self._highlight_in_editor(location_item.text(), 1)
            return

        if self.current_mode == "lexer":
            location_item = self.result_table.item(row, 3)
            if not location_item:
                return
            self._highlight_in_editor(location_item.text(), 1)
            return

    def _highlight_in_editor(self, location_text, length):
        import re
        m = re.match(r"Строка (\d+), позиция (\d+)", location_text)
        if not m:
            return

        line_num = int(m.group(1))
        col_num = int(m.group(2))

        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        for _ in range(line_num - 1):
            cursor.movePosition(cursor.MoveOperation.Down)
        cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.MoveAnchor, col_num - 1)
        cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, length)

        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def _on_show_text_info(self, title, text):
        QMessageBox.information(self, title, text)

    def _on_show_help(self):
        text = (
            "<b>Файл</b><br>"
            "Создать (Ctrl+N) - создание нового документа.<br>"
            "Открыть (Ctrl+O) - открытие текстового файла.<br>"
            "Сохранить (Ctrl+S) - сохранение текущего документа.<br>"
            "Сохранить как (Ctrl+Shift+S) - сохранение под новым именем.<br>"
            "Выход (Alt+F4) - завершение работы программы.<br><br>"
            "<b>Правка</b><br>"
            "Отменить (Ctrl+Z) - отмена последнего действия.<br>"
            "Повторить (Ctrl+Y) - повтор отменённого действия.<br>"
            "Вырезать (Ctrl+X) - удаление выделенного текста в буфер обмена.<br>"
            "Копировать (Ctrl+C) - копирование выделенного текста.<br>"
            "Вставить (Ctrl+V) - вставка текста из буфера обмена.<br>"
            "Удалить (Delete) - удаление выделенного текста.<br>"
            "Выделить всё (Ctrl+A) - выделение всего текста.<br><br>"
            "<b>Текст</b><br>"
            "Содержит информационные разделы, связанные с языковым процессором.<br><br>"
            "<b>Пуск (F5)</b><br>"
            "Лексический анализ - разбор текста на лексемы.<br>"
            "Синтаксический анализ (F6) - проверка структуры объявлений.<br>"
            "Семантический анализ и AST (F8) - построение дерева и проверка семантики.<br>"
            "Внутренняя форма программы (F9) - тетрады и ПОЛИЗ для арифметики.<br>"
            "Поиск подстрок (F7) - поиск ОГРН, комментариев Pascal или RGB-цветов.<br><br>"
            "<b>Справка (F1)</b><br>"
            "Вызов этого руководства и сведений о программе."
        )
        QMessageBox.information(self, "Справка", text)

    def _on_show_about(self):
        text = (
            f"<b>{APP_TITLE}</b><br><br>"
            "Лабораторная работа №6<br>"
            "«Создание внутренней формы представления программы»<br><br>"
            "<b>Тема:</b> Объявление структуры на языке Java<br><br>"
            "<b>Автор:</b> Башинов Арья Игоревич, группа АП-326"
        )
        QMessageBox.about(self, "О программе", text)

    def closeEvent(self, event):
        if self._maybe_save():
            event.accept()
        else:
            event.ignore()


def run():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, Qt.white)
    palette.setColor(QPalette.ColorRole.WindowText, Qt.black)
    palette.setColor(QPalette.ColorRole.Base, Qt.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.black)
    palette.setColor(QPalette.ColorRole.Button, Qt.white)
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.black)
    palette.setColor(QPalette.ColorRole.Highlight, Qt.blue)
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.white)
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    return app.exec()