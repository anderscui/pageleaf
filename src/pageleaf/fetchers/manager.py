# coding=utf-8
import logging
from pathlib import Path

from pageleaf.commons.io.files import json_load, json_dump
from pageleaf.fetchers.arxiv_meta import ArxivMetaFetcher
from pageleaf.fetchers.arxiv_pdf import ArxivPdfFetcher
from pageleaf.fetchers.base import BaseFetcher, RawPaperData, extract_arxiv_id
from pageleaf.fetchers.huggingface import HuggingFacePaperFetcher

logger = logging.getLogger(__name__)


class FetcherManager:
    def __init__(self):
        self.fetchers: list[BaseFetcher] = sorted([
            ArxivMetaFetcher(),
            HuggingFacePaperFetcher(),
            ArxivPdfFetcher(),
        ], key=lambda fetcher: fetcher.priority)

    def fetch(self, identifier: str) -> dict[str, RawPaperData]:
        arxiv_id = extract_arxiv_id(identifier)
        if arxiv_id is None:
            return {}

        save_path = Path.home() / f'data/papers/fetched/{arxiv_id}.json'
        save_path.parent.mkdir(parents=True, exist_ok=True)
        if save_path.exists():
            logger.info(f'Metadata File already exists: {save_path}, skipping download.')
            return json_load(save_path)

        results = {}
        suggested_title = None

        for fetcher in self.fetchers:
            if fetcher.can_handle(identifier):
                if fetcher.source == 'arxiv' and suggested_title:
                    raw = fetcher.fetch(identifier, suggested_title=suggested_title)
                else:
                    raw = fetcher.fetch(identifier)

                if raw:
                    results[fetcher.source] = raw
                    if not suggested_title and fetcher.source in {'arxiv_api', 'huggingface'}:
                        suggested_title = raw.payload.get('data', {}).get('title')
                        logger.debug(f'got title from {fetcher.source}')

        json_dump({k: v.model_dump() for k, v in results.items()}, save_path, indent=2)
        return results


if __name__ == '__main__':
    # identifier = 'https://arxiv.org/abs/2501.12948'
    # identifier = 'https://arxiv.org/abs/2601.04720'
    identifier = '2512.16301'
    fm = FetcherManager()

    print(fm.fetch(identifier))
