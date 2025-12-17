# coding=utf-8
from pageleaf.fetchers.arxiv import ArxivFetcher
from pageleaf.fetchers.base import BaseFetcher, RawPaperData
from pageleaf.fetchers.huggingface import HuggingFacePaperFetcher


class FetcherManager:
    def __init__(self):
        self.fetchers: list[BaseFetcher] = sorted([
            HuggingFacePaperFetcher(),
            ArxivFetcher(),
        ], key=lambda fetcher: fetcher.priority)

    def fetch(self, identifier: str) -> dict[str, RawPaperData]:
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
                    if fetcher.source == 'huggingface':
                        suggested_title = raw.payload.get('title')

        return results


if __name__ == '__main__':
    identifier = 'https://arxiv.org/abs/2501.12948'
    fm = FetcherManager()

    print(fm.fetch(identifier))
