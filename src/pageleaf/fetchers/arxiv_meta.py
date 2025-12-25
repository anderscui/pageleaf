# coding=utf-8
import logging
from pathlib import Path

import arxiv

from pageleaf.commons.io.files import json_dump
from pageleaf.fetchers.base import BaseFetcher, extract_arxiv_id, RawPaperData

logger = logging.getLogger(__name__)


class ArxivMetaFetcher(BaseFetcher):
    source = 'arxiv_api'
    priority = 9

    def can_handle(self, identifier: str) -> bool:
        return extract_arxiv_id(identifier) is not None

    def fetch(self, identifier: str):
        arxiv_id = extract_arxiv_id(identifier)
        if not arxiv_id:
            return None

        save_path = Path.home() / f'data/papers/arxiv/{arxiv_id}.json'
        save_path.parent.mkdir(parents=True, exist_ok=True)
        if save_path.exists():
            logger.info(f'Metadata File already exists: {save_path}, skipping download.')
            return RawPaperData(
                source=self.source,
                external_ids={'arxiv': arxiv_id},
                payload={'json_path': str(save_path)}
            )

        try:
            search = arxiv.Search(id_list=[arxiv_id])
            paper = next(arxiv.Client().results(search))

            converted = {
                'id': paper.entry_id,
                'short_id': paper.get_short_id(),
                'title': paper.title,
                'summary': paper.summary,

                'published': paper.published.isoformat() if paper.published else None,
                'updated': paper.updated.isoformat() if paper.updated else None,

                'categories': paper.categories,
                'primary_category': paper.primary_category,
                'authors': [author.name for author in paper.authors],

                'links': [{'href': link.href, 'rel': link.rel, 'content-type': link.content_type, 'title': link.title} for link in paper.links],
                'pdf_url': paper.pdf_url,
                'source_url': paper.source_url(),
                'doi': paper.doi,
                'comment': paper.comment,
            }

            json_dump(converted, save_path, indent=2)

            return RawPaperData(
                source=self.source,
                external_ids={'arxiv': arxiv_id},
                payload=converted
            )
        except Exception as e:
            logger.error(f'Arxiv Metadata Fetch Error: {e}')
        return None


if __name__ == '__main__':
    fetcher = ArxivMetaFetcher()
    identifier = 'https://huggingface.co/papers/2511.21631'
    print(fetcher.fetch(identifier).model_dump_json(indent=2))
