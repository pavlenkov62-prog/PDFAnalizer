from dataclasses import dataclass, field


# ---------------------------------------------------------
# Минимальная единица текста
# ---------------------------------------------------------

@dataclass
class TextSpan:

    text: str = ""

    translated_text: str = ""

    font: str = ""

    size: float = 0.0

    color: int = 0

    flags: int = 0

    bbox: tuple = (0, 0, 0, 0)

    current_bbox: tuple = None

    origin: tuple = (0, 0)

    ascender: float = 0.0

    descender: float = 0.0
    def __post_init__(self):

        if self.current_bbox is None:
            self.current_bbox = self.bbox


# ---------------------------------------------------------
# Строка
# ---------------------------------------------------------

@dataclass
class TextLine:

    spans: list[TextSpan] = field(default_factory=list)

    bbox: tuple = (0, 0, 0, 0)

    @property
    def text(self):

        return "".join(span.text for span in self.spans)


# ---------------------------------------------------------
# Текстовый блок
# ---------------------------------------------------------

@dataclass
class TextBlock:

    page: int = 0

    number: int = 0

    bbox: tuple = (0, 0, 0, 0)

    lines: list[TextLine] = field(default_factory=list)

    translated_text: str = ""
    current_bbox: tuple = None

    need_translate: bool = True
    style_id: int = -1

    @property
    def text(self):

        return "\n".join(line.text for line in self.lines)
    def __post_init__(self):

        if self.current_bbox is None:
            self.current_bbox = self.bbox
            
# ---------------------------------------------------------
# Изображение
# ---------------------------------------------------------

@dataclass
class ImageBlock:

    bbox: tuple = (0, 0, 0, 0)

# ---------------------------------------------------------
# Страница
# ---------------------------------------------------------

@dataclass
class PageInfo:

    number: int = 0

    width: float = 0

    height: float = 0

    rotation: int = 0

    blocks: list[TextBlock] = field(default_factory=list)
    images: list[ImageBlock] = field(default_factory=list)


# ---------------------------------------------------------
# Документ
# ---------------------------------------------------------

@dataclass
class PdfDocument:

    filename: str = ""

    page_count: int = 0

    file_size: int = 0

    has_links: bool = False

    has_toc: bool = False

    toc: list = field(default_factory=list)

    pages: list[PageInfo] = field(default_factory=list)