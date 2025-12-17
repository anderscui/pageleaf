# coding=utf-8
import logging

import httpx

from pageleaf.fetchers.base import BaseFetcher, extract_arxiv_id, RawPaperData

logger = logging.getLogger(__name__)


class HuggingFacePaperFetcher(BaseFetcher):
    source = 'huggingface'
    priority = 10

    def __init__(self, base_url: str = 'https://huggingface.co/api/papers'):
        self.base_url = base_url

    def can_handle(self, identifier: str) -> bool:
        return extract_arxiv_id(identifier) is not None

    def fetch(self, identifier: str):
        arxiv_id = extract_arxiv_id(identifier)
        if not arxiv_id:
            return None

        url = f'{self.base_url}/{arxiv_id}'
        try:
            with httpx.Client() as client:
                resp = client.get(url, timeout=10.0)
                logger.debug(f'headers: {resp.headers}')
                if resp.status_code == 200:
                    data = resp.json()
                    return RawPaperData(
                        source=self.source,
                        external_ids={'arxiv': arxiv_id},
                        payload=data
                    )
        except Exception as e:
            logger.error(f'HF Fetch Error: {e}')
        return None


if __name__ == '__main__':
    import json

    # headers: Headers({'content-type': 'application/json; charset=utf-8', 'content-length': '22083', 'connection': 'keep-alive', 'date': 'Wed, 17 Dec 2025 11:27:22 GMT', 'etag': 'W/"5643-Rs0BFWd6yP2Ek3c/HwHdTuttK08"', 'x-powered-by': 'huggingface-moon', 'x-request-id': 'Root=1-6942939a-0d457c5851fb776f45a366cf', 'ratelimit': '"api";r=9999;t=158', 'ratelimit-policy': '"fixed window";"api";q=10000;w=300', 'cross-origin-opener-policy': 'same-origin', 'referrer-policy': 'strict-origin-when-cross-origin', 'access-control-max-age': '86400', 'access-control-allow-origin': 'https://huggingface.co', 'vary': 'Origin', 'access-control-expose-headers': 'X-Repo-Commit,X-Request-Id,X-Error-Code,X-Error-Message,X-Total-Count,ETag,Link,Accept-Ranges,Content-Range,X-Linked-Size,X-Linked-ETag,X-Xet-Hash', 'x-cache': 'Miss from cloudfront', 'via': '1.1 5519434325290aca21702ef9e3fa5194.cloudfront.net (CloudFront)', 'x-amz-cf-pop': 'NRT12-P2', 'x-amz-cf-id': 'JMe-2hXZTGrU2HiDziujJdYQEnVTWGTVTTTiauO5XK4H7nA3Imob6Q=='})
    fetcher = HuggingFacePaperFetcher()
    identifier = 'https://arxiv.org/abs/2512.02556'
    fetched = fetcher.fetch(identifier)
    print(json.dumps(fetched.payload, indent=2, ensure_ascii=False))
