# coding=utf-8
from pathlib import Path

import fitz


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


def extract_blocks(pdf_path):
    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            # print(dir(page))
            blocks = page.get_text('blocks')
            for block in blocks:
                if block[-1] != 0:
                    print('image block:', block)
        print('\n')


def extract_dict(pdf_path):
    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            # print(dir(page))
            blocks = page.get_text('dict')
            # page: dict_keys(['width', 'height', 'blocks'])

            # text block: dict_keys(['type', 'number', 'flags', 'bbox', 'lines'])
            # image block: dict_keys(['type', 'number', 'bbox', 'width', 'height', 'ext', 'colorspace', 'xres', 'yres', 'bpc', 'transform', 'size', 'image', 'mask'])
            # print(blocks['width'])
            # print(blocks['height'])
            blocks = blocks['blocks']
            for block in blocks:
                block_type = block['type']
                block_num = block['number']
                if block_type == 0:
                    # print('text:', block.keys())
                    # print(block)
                    # print(block['number'])
                    pass
                else:
                    # print('image:', block.keys())
                    # print(block['number'])
                    img_path = save_image_block(block, Path('./'), page_num, block_num)
                    if img_path:
                        print('image:', page_num, block_num, block['width'], block['height'], block['bbox'])

            # for block in blocks:
            #     if block[-1] != 0:
            #         print('image block:', block)
            # print(blocks)
            # break
        print('\n')


if __name__ == '__main__':
    file = '/Users/andersc/data/papers/arxiv/2501.12948 - DeepSeek-R1 - Incentivizing Reasoning Capability in LLMs via Reinforcement Learning.pdf'
    # file = '/Users/andersc/data/papers/arxiv/2511.21631 - Qwen3-VL Technical Report.pdf'
    file = '/Users/andersc/Downloads/cool nlp papers/Cognitive Architectures for Language Agents v3 (2024).pdf'
    extract_dict(file)
    # for file in list_files('/Users/andersc/Downloads/cool nlp papers', '*.pdf'):
    #     print(file)
    #     extract_blocks(file)
    #     print()
