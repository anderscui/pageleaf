# coding=utf-8
import logging
import sys
from pathlib import Path

import httpx

from pageleaf.fetchers.base import BaseFetcher, extract_arxiv_id, RawPaperData, sanitize_filename

logger = logging.getLogger(__name__)


class ArxivFetcher(BaseFetcher):
    source = 'arxiv'
    priority = 100

    def can_handle(self, identifier: str) -> bool:
        return extract_arxiv_id(identifier) is not None

    def fetch(self, identifier: str, suggested_title: str = None):
        arxiv_id = extract_arxiv_id(identifier)
        if not arxiv_id:
            return None

        if suggested_title:
            clean_title = sanitize_filename(suggested_title)
            filename = f'{arxiv_id} - {clean_title}.pdf'
        else:
            filename = f'{arxiv_id}.pdf'
        save_path = Path.home() / f'data/papers/arxiv/{filename}'
        save_path.parent.mkdir(parents=True, exist_ok=True)

        if save_path.exists():
            logger.info(f'File already exists: {save_path}, skipping download.')
            return RawPaperData(
                source=self.source,
                external_ids={'arxiv': arxiv_id},
                payload={'pdf_path': str(save_path)}
            )

        # TODO: multi versions support
        pdf_url = f'https://arxiv.org/pdf/{arxiv_id}'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0',
        }
        try:
            with httpx.Client(headers=headers, follow_redirects=True) as client:
                with client.stream('GET', pdf_url) as resp:
                    if resp.status_code != 200:
                        logger.warning(f'Arxiv download pdf failed, code: {resp.status_code}')
                        return None

                    logger.debug(f'headers: {resp.headers}')
                    total_size = int(resp.headers.get('Content-Length', 0))
                    downloaded = 0

                    with open(save_path, 'wb') as f:
                        print('is atty:', sys.stdout.isatty())
                        for chunk in resp.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)

                            if total_size > 0 and sys.stdout.isatty():
                                percent = downloaded / total_size * 100
                                sys.stdout.write(f'\r[Fetcher] Progress: {percent:.1f}%')
                                sys.stdout.flush()
                    if sys.stdout.isatty():
                        print()

            return RawPaperData(
                source=self.source,
                external_ids={'arxiv': arxiv_id},
                payload={'pdf_path': str(save_path)}
            )
        except Exception as e:
            logger.error(f'Arxiv Fetch Error: {e}')
        return None


if __name__ == '__main__':
    # headers: Headers({'connection': 'keep-alive', 'content-length': '980616', 'access-control-allow-origin': '*',
    # 'link': "<https://arxiv.org/pdf/2512.02556>; rel='canonical'",
    # 'content-type': 'application/pdf', 'server': 'Google Frontend', 'via': '1.1 google, 1.1 varnish, 1.1 varnish, 1.1 varnish',
    # 'x-cloud-trace-context': '4e704c39ffb977099e52474a5df9b5f2', 'etag': 'CJ6725qnoJEDEAI=', 'content-disposition': 'inline; filename="2512.02556v1.pdf"',
    # 'last-modified': 'Wed, 03 Dec 2025 01:51:27 GMT', 'accept-ranges': 'bytes', 'age': '1240879',
    # 'date': 'Wed, 17 Dec 2025 11:21:32 GMT', 'x-served-by': 'cache-lga21990-LGA, cache-lga21939-LGA, cache-nrt-rjtf7700093-NRT', 'x-cache': 'MISS, MISS, HIT', 'x-timer': 'S1765970492.045582,VS0,VE1'})
    # source='arxiv' external_ids={'arxiv': '2512.02556'} payload={'pdf_path': '/Users/andersc/data/papers/arxiv/2512.02556.pdf'}
    fetcher = ArxivFetcher()
    # identifier = 'https://arxiv.org/abs/2512.02556'
    # print(fetcher.fetch(identifier, suggested_title='DeepSeek-V3.2: Pushing the Frontier of Open Large Language Models'))

    # identifier = 'https://arxiv.org/abs/2511.22699'
    # print(fetcher.fetch(identifier, suggested_title='Z-Image: An Efficient Image Generation Foundation Model with Single-Stream Diffusion Transformer'))

    identifier = 'https://huggingface.co/papers/2511.21631'
    print(fetcher.fetch(identifier, suggested_title='Qwen3-VL Technical Report'))
