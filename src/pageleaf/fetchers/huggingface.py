# coding=utf-8
from pageleaf.fetchers.base import BaseFetcher


class HuggingFacePaperFetcher(BaseFetcher):
    source = 'huggingface'

    def fetch(self, identifier: str):
        # call https://huggingface.co/api/papers/{id}
        return RawPaperData(...)
