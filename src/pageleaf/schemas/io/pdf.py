# coding=utf-8
from pathlib import Path

import fitz
from pydantic import BaseModel, PrivateAttr, Field

from pageleaf.commons.iterable import rename_keys


def save_image_block(
        image_block: dict,
        output_dir: Path,
        page_index: int,
        block_index: int,
        min_width: float = 30.0,
        min_height: float = 30.0
) -> Path | None:

    x0, y0, x1, y1 = image_block['bbox']
    width = x1 - x0
    height = y1 - y0
    if width < min_width or height < min_height:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)

    image_data = image_block['image']
    image_ext = image_block['ext']

    image_path = output_dir / f'page_{page_index}_img_{block_index}.{image_ext}'
    with open(image_path, 'wb') as f:
        f.write(image_data)

    return image_path


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
    chars: list = Field(default_factory=list)

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

    # @property
    # def height(self):
    #     return self.bbox[3] - self.bbox[1]
    #
    # @property
    # def y_center(self):
    #     return (self.bbox[1] + self.bbox[3]) / 2


class PdfBlock(BaseModel):
    _text: str = PrivateAttr(default=None)

    page_number: int

    type: int
    block_number: int
    bbox: tuple[float, float, float, float]

    lines: list[PdfLine] = Field(default_factory=list)

    object_type: str = 'block'

    @classmethod
    def load(cls, data: dict, page_number, image_dir: Path | None = None):
        _type = data['type']
        if _type == 0:
            return TextBlock.load(data, page_number)
        elif _type == 1:
            return ImageBlock.load(data, page_number, image_dir=image_dir)
        return None

    def is_text(self):
        return self.type == 0

    def is_image(self):
        return self.type == 1

    @property
    def text(self) -> str | None:
        return None

    @property
    def is_single_line(self):
        return len(self.lines) == 1


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

    # width and height of original image.
    width: int
    height: int

    ext: str
    image: bytes | None = None
    image_path: Path | None = None
    mask: bytes | None = None


    @classmethod
    def load(cls, data: dict, page_number: int, image_dir: Path | None = None):
        data['block_number'] = data.pop('number', None)
        data['page_number'] = page_number

        if image_dir:
            saved_path = save_image_block(data, image_dir, page_number, data['block_number'])
            if not saved_path:
                return None
            data['image_path'] = saved_path
            data.pop('image', None)

        return cls.model_validate(data)

    @property
    def size(self):
        if self.image is not None:
            return len(self.image)
        if self.image_path and self.image_path.exists():
            return self.image_path.stat().st_size
        return 0

    @property
    def persisted(self):
        return self.image_path is not None


class PdfPage(BaseModel):
    page_number: int

    height: float
    width: float
    blocks: list[PdfBlock]

    object_type: str = 'page'

    @classmethod
    def load(cls, data: dict, page_number, image_dir: Path | None = None):
        data['page_number'] = page_number
        blocks = data.get('blocks') or []
        if not blocks:
            return None

        blocks = [PdfBlock.load(block, page_number, image_dir) for block in blocks]
        blocks = [block for block in blocks if block is not None]
        data['blocks'] = blocks
        return cls.model_validate(data)


class PdfDocument(BaseModel):
    pages: list[PdfPage]

    object_type: str = 'document'

    @classmethod
    def load_file(cls, file_path: str, image_dir: str | Path | None = None):
        if image_dir:
            image_dir = Path(image_dir)

        pages = []
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    page_number = page.number + 1
                    page_obj = page.get_text('dict')
                    page_loaded = PdfPage.load(page_obj, page_number, image_dir)
                    if page_loaded is None:
                        continue
                    pages.append(page_loaded)
        except Exception as e:
            print(f'Error loading {file_path}: {e}')

        return cls(pages=pages)


if __name__ == '__main__':
    # file = '/Users/andersc/Downloads/cool nlp papers/Cognitive Architectures for Language Agents v3 (2024).pdf'
    file = '/Users/andersc/data/papers/arxiv/2511.21631 - Qwen3-VL Technical Report.pdf'
    doc = PdfDocument.load_file(file, image_dir='./')
    print(f'pages: {len(doc.pages)}')
    for page in doc.pages:
        print(f'page {page.page_number}: ({page.width}, {page.height}), {len(page.blocks)} blocks:')

        for block in page.blocks:
            print(f'block: {block.type}, {block.page_number}, {block.block_number}')
            if block.is_text():
                print(block.text[:100])
                print()
            else:
                if block.image_path:
                    print('image:', block.image_path)
                    print()

        print('\n')
