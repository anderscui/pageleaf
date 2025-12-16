# coding=utf-8
from pageleaf.fetchers.base import BaseFetcher


class ArxivFetcher(BaseFetcher):
    source = 'arxiv'

    def fetch(self, identifier: str):
        # metadata + pdf download
        return RawPaperData(...)
