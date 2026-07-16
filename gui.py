from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QSpinBox,
    QSplitter,
    QSizePolicy,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem
)

from PySide6.QtGui import (
    QPixmap,
    QPainter,
    QPen,
    QColor,
    QFontMetricsF
)

from PySide6.QtCore import Qt

from pdf_engine import PdfEngine
from translator import Translator
from style_classifier import StyleClassifier

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.engine = PdfEngine()
        self.translator = Translator()
        self.style_classifier = StyleClassifier()
        self.document = None

        self.setWindowTitle("PDF Translator")
        self.resize(1100, 800)
        self.showMaximized()

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # ---------- Верхняя панель ----------

        row = QHBoxLayout()

        row.addWidget(QLabel("PDF"))

        self.edFile = QLineEdit()
        self.edFile.setReadOnly(True)
        row.addWidget(self.edFile)

        self.btnOpen = QPushButton("Выбрать PDF")
        self.btnOpen.clicked.connect(self.open_pdf)
        row.addWidget(self.btnOpen)

        layout.addLayout(row)

        # ---------- Панель управления ----------

        row2 = QHBoxLayout()

        row2.addWidget(QLabel("Страница"))

        self.btnPrev = QPushButton("◀")
        self.btnPrev.setEnabled(False)
        self.btnPrev.clicked.connect(self.prev_page)
        row2.addWidget(self.btnPrev)

        self.spin = QSpinBox()
        self.spin.setMinimum(1)
        self.spin.setMaximum(1)
        self.spin.valueChanged.connect(self.page_changed)
        row2.addWidget(self.spin)

        self.btnNext = QPushButton("▶")
        self.btnNext.setEnabled(False)
        self.btnNext.clicked.connect(self.next_page)
        row2.addWidget(self.btnNext)

        row2.addSpacing(20)

        row2.addWidget(QLabel("Блок"))

        self.spinBlock = QSpinBox()
        self.spinBlock.setMinimum(1)
        self.spinBlock.setMaximum(1)
        self.spinBlock.setEnabled(False)
        self.spinBlock.valueChanged.connect(self.block_changed)
        row2.addWidget(self.spinBlock)
        self.lblBlockInfo = QLabel("Тип: -    Style: -    Span: -")

        font = self.lblBlockInfo.font()
        font.setBold(True)
        self.lblBlockInfo.setFont(font)
        self.lblBlockInfo.setMinimumWidth(320)

        row2.addWidget(self.lblBlockInfo)

        row2.addSpacing(20)
        

        self.btnTranslate = QPushButton("Перевести блок")
        self.btnTranslate.setEnabled(False)
        self.btnTranslate.clicked.connect(self.translate_block)
        row2.addWidget(self.btnTranslate)

        self.btnUndo = QPushButton("Undo")
        self.btnUndo.setEnabled(False)
        self.btnUndo.clicked.connect(self.undo_translation)
        row2.addWidget(self.btnUndo)

        self.btnBlockInfo = QPushButton("Свойства блока")
        self.btnTranslatePage = QPushButton("Перевести страницу")
        self.btnTranslatePage.setEnabled(False)
        self.btnTranslatePage.clicked.connect(self.translate_page)
        row2.addWidget(self.btnTranslatePage)

        row2.addStretch()

        layout.addLayout(row2)

                # ---------- Нижняя часть окна ----------

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.splitter)

        # ---------- Левая панель ----------

        left = QWidget()
        leftLayout = QVBoxLayout(left)

        leftLayout.addWidget(QLabel("Информация"))

        self.lblDocInfo = QLabel()
        leftLayout.addWidget(self.lblDocInfo)

        self.info = QTextEdit()
        self.info.setMaximumHeight(180)
        self.info.setReadOnly(True)
        leftLayout.addWidget(self.info)

        leftLayout.addWidget(QLabel("Блоки"))

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        leftLayout.addWidget(self.text)
        leftLayout.addWidget(QLabel("Перевод"))

        self.translation = QTextEdit()
        self.translation.setReadOnly(True)
        leftLayout.addWidget(self.translation)

        self.splitter.addWidget(left)

        # ---------- Правая панель ----------

        right = QWidget()
        rightLayout = QVBoxLayout(right)

        rightLayout.addWidget(QLabel("Страница"))

        self.pageView = QGraphicsView()

        self.scene = QGraphicsScene(self)

        self.pageView.setScene(self.scene)

        self.pagePixmap = QGraphicsPixmapItem()

        self.scene.addItem(self.pagePixmap)

        self.pageView.setStyleSheet("""
            QGraphicsView {
                border: 1px solid gray;
                background: white;
            }
        """)

        self.pageView.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.pageView.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        rightLayout.addWidget(self.pageView)

        self.splitter.addWidget(right)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setHandleWidth(2)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background: #808080;
            }
        """)

    def open_pdf(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Выберите PDF", "", "PDF (*.pdf)"
        )
        if not filename:
            return

        self.document = self.engine.load(filename)
        self.edFile.setText(filename)
        self.spin.setMaximum(self.document.page_count)
        self.spin.setValue(1)
        self.show_blocks()
        self.btnPrev.setEnabled(True)
        self.btnNext.setEnabled(True)
        self.spinBlock.setEnabled(True)
        self.btnTranslate.setEnabled(True)
        self.btnTranslatePage.setEnabled(True)
        self.btnUndo.setEnabled(True)
    

        pages_with_text = sum(1 for p in self.document.pages if p.blocks)
        empty_pages = self.document.page_count - pages_with_text
        size_mb = self.document.file_size / 1024 / 1024

        self.lblDocInfo.setText(
            f"Страниц: {self.document.page_count}    "
            f"Размер: {size_mb:.2f} МБ"
        )


    def show_blocks(self):
        if self.document is None:
            return

        page = self.document.pages[self.spin.value() - 1]
        styles = self.style_classifier.classify(page)
        single_count = sum(
            1 for b in page.blocks
            if len(b.lines) == 1
        )

        paragraph_count = len(page.blocks) - single_count

        self.info.clear()

        self.info.append(
            f"Страница : {self.spin.value()} / {self.document.page_count}"
        )

        self.info.append("")

        self.info.append(
            f"Размер : {page.width:.2f} × {page.height:.2f}"
        )

        self.info.append("")

        self.info.append(
            f"Блоков : {len(page.blocks)}"
        )

        self.info.append(
            f"SingleLine : {single_count}"
        )

        self.info.append(
            f"Paragraph : {paragraph_count}"
        )

        self.info.append(
            f"Graphics : {len(page.images)}"
        )
        self.info.append(
            f"Styles : {len(styles)}"
        )
        self.show_page()
        self.current_page = page
        self.spinBlock.setMaximum(max(1, len(page.blocks)))
        self.spinBlock.setValue(1)

        self.inspect_selected_block()

    def inspect_block(self):

        if not hasattr(self, "current_page"):
            self.info.append("")
            self.info.append("Сначала нажмите 'Показать блоки'.")
            return

        self.info.append("")
        self.info.append(f"Страница содержит {len(self.current_page.blocks)} блоков.")
        if not self.current_page.blocks:
            return

        block = self.current_page.blocks[0]

        self.info.append("")
        self.info.append("Первый блок")
        self.info.append(f"Номер : {block.number}")
        self.info.append(f"BBox  : {block.bbox}")

        if block.lines and block.lines[0].spans:

            span = block.lines[0].spans[0]

            self.info.append("")
            self.info.append(f"Шрифт : {span.font}")
            self.info.append(f"Размер: {span.size}")
            self.info.append(f"Flags : {span.flags}")
            self.info.append(f"Origin: {getattr(span, 'origin', 'НЕТ')}")
            self.info.append(f"Asc   : {getattr(span, 'ascender', 'НЕТ')}")
            self.info.append(f"Desc  : {getattr(span, 'descender', 'НЕТ')}")

    def is_single_line(self, block):

        if not block.lines:
            return False

        first = None
        min_y = None
        max_y = None

        for line in block.lines:

            if not line.spans:
                continue

            span = line.spans[0]

            if first is None:
                first = span
                min_y = span.origin[1]
                max_y = span.origin[1]
            else:
                if span.origin[1] < min_y:
                    min_y = span.origin[1]

                if span.origin[1] > max_y:
                    max_y = span.origin[1]

        if first is None:
            return False

        return (max_y - min_y) < first.size

    def inspect_selected_block(self):

        if self.document is None:
            return

        page = self.document.pages[self.spin.value() - 1]

        if not page.blocks:
            self.text.clear()
            return

        index = self.spinBlock.value() - 1

        if index < 0 or index >= len(page.blocks):
            return

        block = page.blocks[index]

        self.text.clear()

        if self.is_single_line(block):
            block_type = "SingleLine"
        else:
            block_type = "Paragraph"

        span_count = sum(len(line.spans) for line in block.lines)

        self.lblBlockInfo.setText(
            f"Тип: {block_type}    "
            f"Style: {block.style_id}    "
            f"Span: {span_count}"
        )

        if block.lines and block.lines[0].spans:

            span = block.lines[0].spans[0]

            flags = span.flags

            bold = "Да" if (flags & 16) else "Нет"
            italic = "Да" if (flags & 2) else "Нет"
            serif = "Да" if (flags & 4) else "Нет"
            mono = "Да" if (flags & 8) else "Нет"

            self.text.append("")
            self.text.append("Стиль")
            self.text.append(f"Font      : {span.font}")
            self.text.append(f"Size      : {round(span.size)}")
            self.text.append(f"Bold      : {bold}")
            self.text.append(f"Italic    : {italic}")
            self.text.append(f"Serif     : {serif}")
            self.text.append(f"Monospace : {mono}")

        self.text.append("")
        self.text.append("Текст")
        self.text.append(block.text)

    def show_page(self):

        if self.document is None:
            return

        selected = -1

        if hasattr(self, "current_page"):
            selected = self.spinBlock.value() - 1

        image = self.engine.render_page(
            self.document.filename,
            self.spin.value(),
            selected
        )
        page = self.document.pages[self.spin.value() - 1]

        if page.width > page.height:
            self.splitter.setSizes([300, 1300])
        else:
           self.splitter.setSizes([450, 1050])
        painter = QPainter(image)

        page = self.document.pages[self.spin.value() - 1]

        scale = 1.5

        #
        # Закрашиваем английский текст
        #

        for block in page.blocks:

            if block.translated_text == "":
                continue

            if self.is_single_line(block):

                for line in block.lines:

                    for span in line.spans:

                        if (
                            span.translated_text == ""
                            or span.translated_text == span.text
                        ):
                            continue

                        sx0, sy0, sx1, sy1 = span.current_bbox

                        painter.fillRect(
                            int(sx0 * scale),
                            int(sy0 * scale),
                            int((sx1 - sx0) * scale),
                            int((sy1 - sy0) * scale),
                            QColor(255, 255, 255)
                        )

            else:

                x0, y0, x1, y1 = block.current_bbox

                painter.fillRect(
                    int(x0 * scale),
                    int(y0 * scale),
                    int((x1 - x0) * scale),
                    int((y1 - y0) * scale),
                    QColor(255, 255, 255)
                )

        #
        # Рисуем русский текст
        #

        pen = QPen(QColor(0, 0, 0))
        painter.setPen(pen)

        font = painter.font()

        for block in page.blocks:

            if block.translated_text == "":
                continue

            if len(block.lines) > 0 and len(block.lines[0].spans) > 0:

                size = block.lines[0].spans[0].size
                size = max(6, size)

                font.setPointSizeF(size)
                font.setBold(True)
                painter.setFont(font)

            x0, y0, x1, y1 = block.current_bbox

            #
            # Авторасширение SingleLine
            #
            if self.is_single_line(block):

                metrics = QFontMetricsF(font)

                needed = metrics.horizontalAdvance(
                    block.translated_text
                )
                original = metrics.horizontalAdvance(
                    block.text
                )

                current = x1 - x0

                if original > 1:

                    scale_factor = current / original

                    needed *= scale_factor

                current = x1 - x0

                if needed + 8 > current:

                    block.current_bbox = (
                        x0,
                        y0,
                        x0 + needed * 0.78 + 4,
                        y1
                    )

                    x0, y0, x1, y1 = block.current_bbox

            flags = (
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignTop
            )

            if not self.is_single_line(block):
                flags |= Qt.TextFlag.TextWordWrap

            if self.is_single_line(block):

                for line in block.lines:

                    for span in line.spans:

                        sx0, sy0, sx1, sy1 = span.current_bbox

                        if (
                            span.translated_text == ""
                            or span.translated_text == span.text
                        ):
                            continue

                        painter.drawText(
                            int(sx0 * scale),
                            int(span.origin[1] * scale),
                            span.translated_text
                        )

            else:

                painter.drawText(
                    int(x0 * scale),
                    int(y0 * scale),
                    int((x1 - x0) * scale),
                    int((y1 - y0) * scale),
                    flags,
                    block.translated_text
                )

        #
        # Синие рамки текстовых блоков
        #

        for block in page.blocks:

            if self.is_single_line(block):
               pen = QPen(QColor(0, 0, 255))
            else:
               pen = QPen(QColor(255, 140, 0))

            pen.setWidth(2)
            painter.setPen(pen)

            x0, y0, x1, y1 = block.current_bbox

            painter.drawRect(
                int(x0 * scale),
                int(y0 * scale),
                int((x1 - x0) * scale),
                int((y1 - y0) * scale)
            )

        #
        # Зеленые рамки изображений
        #

        pen = QPen(QColor(0, 180, 0))
        pen.setWidth(2)

        painter.setPen(pen)

        for img in page.images:

            x0, y0, x1, y1 = img.bbox

            painter.drawRect(
                int(x0 * scale),
                int(y0 * scale),
                int((x1 - x0) * scale),
                int((y1 - y0) * scale)
            )

        #
        # Красная рамка выбранного блока
        #

        if self.spinBlock.value() > 0:

            block = page.blocks[self.spinBlock.value() - 1]

            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(3)

            painter.setPen(pen)

            x0, y0, x1, y1 = block.current_bbox

            painter.drawRect(
                int(x0 * scale),
                int(y0 * scale),
                int((x1 - x0) * scale),
                int((y1 - y0) * scale)
            )

        painter.end()

        pixmap = QPixmap.fromImage(image)

        self.pagePixmap.setPixmap(pixmap)

        self.scene.setSceneRect(pixmap.rect())

        self.pageView.fitInView(
            self.scene.sceneRect(),
            Qt.AspectRatioMode.KeepAspectRatio
        )

    def page_clicked(self, x, y):

        if self.document is None:
            return

        if not hasattr(self, "current_page"):
            return

        #
        # Координаты сцены -> координаты PDF
        #

        zoom = 1.5

        pdf_x = x / zoom
        pdf_y = y / zoom

        block_no = self.engine.find_block(
            self.document.filename,
            self.spin.value(),
            pdf_x,
            pdf_y
        )

        print(
            f"Scene: ({x:.1f}, {y:.1f})   "
            f"PDF: ({pdf_x:.1f}, {pdf_y:.1f})   "
            f"Block: {block_no}"
        )

        if block_no >= 0:

            self.spinBlock.setValue(block_no + 1)
            self.inspect_selected_block()   

    def translate_block(self):

        if not hasattr(self, "current_page"):
            return

        if not self.current_page.blocks:
            return

        index = self.spinBlock.value() - 1

        if index < 0 or index >= len(self.current_page.blocks):
            return

        block = self.current_page.blocks[index]

        self.translation.clear()
        self.translation.append("Оригинал")
        self.translation.append("")
        self.translation.append(block.text)
        self.translation.append("")
        self.translation.append("-" * 60)
        self.translation.append("")
        self.translation.append("Перевод")
        self.translation.append("")

        try:

            self.translate_one_block(block)

            self.translation.append(block.translated_text)

            self.show_page()

            self.inspect_selected_block()

        except Exception as e:

            self.translation.append(f"Ошибка перевода:\n{e}")

    def translate_one_block(self, block):

        text = block.text.strip()

        if text == "":
            return

        #
        # Тип С (SingleLine)
        #

        if self.is_single_line(block):

            for line in block.lines:

                for span in line.spans:

                    span.translated_text = ""

                    txt = span.text.strip()

                    if txt == "":
                        continue

                    # Только числа
                    if txt.replace(".", "").replace(",", "").isdigit():
                        span.translated_text = span.text
                        block.translated_text += span.translated_text
                        continue

                    # Один символ
                    if len(txt) == 1:
                        span.translated_text = span.text
                        block.translated_text += span.translated_text
                        continue

                    # Нет букв
                    if not any(ch.isalpha() for ch in txt):
                        span.translated_text = span.text
                        block.translated_text += span.translated_text
                        continue

                    span.translated_text = self.translator.translate(span.text)
                    block.translated_text += span.translated_text

            return

        #
        # Тип П (Paragraph)
        #

        if text.replace(".", "").replace(",", "").isdigit():
            return

        if len(text) == 1:
            return

        if not any(ch.isalpha() for ch in text):
            return

        block.translated_text = self.translator.translate(text)

    def prev_page(self):

        if self.spin.value() > 1:
            self.spin.setValue(self.spin.value() - 1)


    def next_page(self):

        if self.document is None:
            return

        if self.spin.value() < self.document.page_count:
            self.spin.setValue(self.spin.value() + 1)


    def page_changed(self):

        if self.document is None:
            return

        self.show_blocks()

    def translate_page(self):

        page = self.document.pages[self.spin.value() - 1]

        for block in page.blocks:

            self.translate_one_block(block)

        self.show_page()

    def undo_translation(self):

        page = self.document.pages[self.spin.value() - 1]

        for block in page.blocks:
            block.translated_text = ""

        self.show_page()

    def block_changed(self):

        self.show_page()
        self.inspect_selected_block()