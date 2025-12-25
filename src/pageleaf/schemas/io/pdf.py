# coding=utf-8
import fitz
from pydantic import BaseModel, PrivateAttr

from pageleaf.commons.iterable import rename_keys


class PdfFont(BaseModel):
    font_name: str
    font_size: float
    font_color: int

    is_bold: bool
    is_italic: bool
    is_monospaced: bool


class PdfSpan(BaseModel):
    page_number: int
    origin: tuple[float, float]
    bbox: tuple[float, float, float, float]

    text: str

    font_name: str
    font_size: float
    font_color: int
    ascender: float
    descender: float

    flags: int

    # not required in most cases
    chars: list = []

    @classmethod
    def load(cls, data: dict, page_number):
        data = rename_keys(data, {
            'font': 'font_name',
            'size': 'font_size',
            'color': 'font_color'
        })
        data['page_number'] = page_number
        # data['origin'] = data['origin']
        # data['bbox'] = data['bbox']

        return cls.model_validate(data)

    @property
    def font(self):
        return PdfFont(font_name=self.font_name,
                       font_size=self.font_size,
                       font_color=self.font_color,
                       is_bold=self.is_bold(),
                       is_italic=self.is_italic(),
                       is_monospaced=self.is_monospaced())

    def is_super_script(self):
        return self.flags & (2 ** 0) > 0

    def is_italic(self):
        return self.flags & (2 ** 1) > 0

    def is_serifed(self):
        return self.flags & (2 ** 2) > 0

    def is_monospaced(self):
        return self.flags & (2 ** 3) > 0

    def is_bold(self):
        return self.flags & (2 ** 4) > 0


class PdfLine(BaseModel):
    _text: str = PrivateAttr(default=None)

    page_number: int
    writing_mode: int
    dir: tuple[float, float] = ()
    bbox: tuple[float, float, float, float] = ()

    spans: list[PdfSpan]

    object_type: str = 'line'

    @classmethod
    def load(cls, data: dict, page_number):
        data = rename_keys(data, {
            'wmode': 'writing_mode',
        })
        data['page_number'] = page_number
        # data['dir'] = Point.from_tuple(data['dir'])
        # data['bbox'] = BoundingBox.from_tuple(data['bbox'])

        spans = data.get('spans') or []
        if not spans:
            return None

        spans = [PdfSpan.load(span, page_number) for span in spans]
        spans = [span for span in spans if span is not None]
        if not spans:
            return None

        data['spans'] = spans
        # span_bboxes = [span.bbox for span in spans]
        # data['bbox'] = BoundingBox.merge(span_bboxes)
        return cls.model_validate(data)

    @property
    def text(self):
        if self._text is None:
            ends = []
            for i, s in enumerate(self.spans):
                if i < len(self.spans) - 1:
                    next_span = self.spans[i + 1]
                    end = '' if next_span.bbox[0] - s.bbox[2] < 0.1 else ' '
                    ends.append(end)
                else:
                    ends.append('')

            self._text = ''.join([s.text + end for s, end in zip(self.spans, ends)])
        return self._text


class PdfBlock(BaseModel):
    _text: str = PrivateAttr(default=None)

    page_number: int

    type: int
    block_number: int
    bbox: tuple[float, float, float, float]

    lines: list[PdfLine] = []

    object_type: str = 'block'

    @classmethod
    def load(cls, data: dict, page_number):
        _type = data['type']
        if _type == 0:
            return TextBlock.load(data, page_number)
        elif _type == 1:
            return ImageBlock.load(data, page_number)
        return None

    def is_text(self):
        return self.type == 0

    def is_image(self):
        return self.type == 1

    @property
    def text(self):
        return None


class TextBlock(PdfBlock):
    type: int = 0

    flags: int

    @classmethod
    def load(cls, data: dict, page_number):
        data['block_number'] = data.pop('number', None)
        data['page_number'] = page_number
        # data['bbox'] = BoundingBox.from_tuple(data['bbox'])

        lines = data.get('lines') or []
        if not lines:
            return None

        lines = [PdfLine.load(line, page_number) for line in lines]
        lines = [line for line in lines if line is not None]
        if not lines:
            return None

        data['lines'] = lines
        return cls.model_validate(data)

    @property
    def text(self):
        if self._text is None:
            self._text = '\n'.join([line.text for line in self.lines])
        return self._text


class ImageBlock(PdfBlock):
    type: int = 1

    ext: str
    image: bytes

    # width and height of original image.
    width: int
    height: int

    mask: bytes | None = None

    @classmethod
    def load(cls, data: dict, page_number: int):
        data['block_number'] = data.pop('number', None)
        data['page_number'] = page_number
        return cls.model_validate(data)

    @property
    def size(self):
        return len(self.image)


class PdfPage(BaseModel):
    page_number: int

    height: float
    width: float
    blocks: list[PdfBlock]

    object_type: str = 'page'

    @classmethod
    def load(cls, data: dict, page_number):
        data['page_number'] = page_number
        blocks = data.get('blocks') or []
        if not blocks:
            return None

        blocks = [PdfBlock.load(block, page_number) for block in blocks]
        blocks = [block for block in blocks if block is not None]
        data['blocks'] = blocks
        return cls.model_validate(data)


class PdfDocument(BaseModel):
    pages: list[PdfPage]

    object_type: str = 'document'

    @classmethod
    def load_file(cls, file_path: str):
        pages = []
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    page_number = page.number + 1
                    page_obj = page.get_text('dict')
                    page_loaded = PdfPage.load(page_obj, page_number)
                    if page_loaded is None:
                        continue
                    pages.append(page_loaded)
        except Exception as e:
            print(f'load pdf file failed: {e}')

        return cls(pages=pages)


if __name__ == '__main__':
    # file = '/Users/andersc/Downloads/cool nlp papers/Cognitive Architectures for Language Agents v3 (2024).pdf'
    file = '/Users/andersc/data/papers/arxiv/2511.21631 - Qwen3-VL Technical Report.pdf'
    doc = PdfDocument.load_file(file)
    print(f'pages: {len(doc.pages)}')
    for page in doc.pages:
        print(f'page {page.page_number}: ({page.width}, {page.height}), {len(page.blocks)} blocks:')

        for block in page.blocks:
            if block.is_text():
                if block.lines:
                    print(block.text)
                    print()
            else:
                print('image:', block.block_number, block.image[:10])

        print('\n')
