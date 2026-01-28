# coding=utf-8
from pathlib import Path

from pageleaf.commons.io.files import json_load
from pageleaf.fetchers.base import extract_arxiv_id
from pageleaf.schemas.paper import Metadata, ExternalIdentifiers


class ArxivIngester:
    def ingest(self, fetched_file: str | Path):
        fetched_file = Path(fetched_file)
        if not fetched_file.exists():
            raise FileNotFoundError(f'`fetched_file` not found: {fetched_file}')

        fetched = json_load(fetched_file)
        # arxiv metadata and pdf file
        required_sources = {'arxiv_api', 'arxiv'}
        missing_sources = required_sources - set(fetched.keys())
        if missing_sources:
            raise ValueError(f'Incomplete paper data, missing keys: {missing_sources}')
        self._merge_data(fetched)

    def _merge_data(self, fetched):
        arxiv_meta = json_load(fetched['arxiv_api']['payload']['json_path'])
        hf_data = None
        if 'huggingface' in fetched:
            hf_data = json_load(fetched['huggingface']['payload']['json_path'])
        arxiv_pdf_file = fetched['arxiv']['payload']['pdf_path']

        arxiv_id = extract_arxiv_id(arxiv_meta['id'])
        metadata = {
            'title': arxiv_meta['title'],
            'abstract': arxiv_meta['summary'],
            'publish_date': arxiv_meta['published'],
            'update_date': arxiv_meta['updated'],
            'authors': arxiv_meta['authors'] or [],
            'primary_category': arxiv_meta['primary_category'],
            'categories': arxiv_meta['categories'],
            'pdf_url': arxiv_meta['pdf_url'],

            'venue': 'arxiv',
            'source': 'arxiv',
            'paper_type': 'preprint',
        }

        if hf_data:
            hf_meta = {
                'hf_ai_summary': hf_data['ai_summary'],
                'hf_ai_keywords': hf_data['ai_keywords'],
                'hf_upvotes': hf_data.get('upvotes') or 0,
                'github_url': hf_data['githubRepo'],
                'github_stars': hf_data['githubStars'],
            }
            metadata.update(hf_meta)

        ids = {
            'arxiv': arxiv_id,
            'doi': arxiv_meta.get('doc') or None
        }
        metadata['external_ids'] = ids

        metadata = Metadata.model_validate(metadata)

        print(metadata.model_dump_json(indent=2))



if __name__ == '__main__':
    ingester = ArxivIngester()
    ingester.ingest('/Users/andersc/data/papers/fetched/2512.16301.json')
