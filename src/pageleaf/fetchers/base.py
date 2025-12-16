# coding=utf-8
from abc import ABC, abstractmethod

import re


def is_valid_arxiv_id(arxiv_id: str) -> bool:
    """
    判断字符串是否是有效的 arXiv paper ID

    支持的格式：
    - 新格式 (2007年4月后): YYMM.NNNNN 或 YYMM.NNNNNvN
      例如: 2301.12345, 2301.12345v1 (4-5 digits)
    - 旧格式 (2007年3月前): archive/YYMMNNN 或 archive.XX/YYMMNNN
      例如: cs/0703001, math.AG/0703001
      archive 可以是: cs, math, physics, astro-ph, cond-mat, gr-qc, hep-ex,
      hep-lat, hep-ph, hep-th, nucl-ex, nucl-th, quant-ph 等

    Args:
        arxiv_id: 待检查的字符串

    Returns:
        bool: 是否是有效的 arXiv ID
    """
    if not arxiv_id or not isinstance(arxiv_id, str):
        return False

    arxiv_id = arxiv_id.strip()

    new_format = r'^\d{4}\.\d{4,5}(v\d+)?$'
    old_format = r'^[a-z\-]+(\.[A-Z]{2})?/\d{7}(v\d+)?$'

    return bool(re.match(new_format, arxiv_id) or re.match(old_format, arxiv_id))


def extract_arxiv_id(url_or_id: str) -> str | None:
    """从URL或直接ID中提取标准的arXiv ID (无版本号)。"""
    # 匹配标准 ID，例如 2401.01234 或 2401.01234v1
    match = re.search(r'(\d{4}\.\d{5}v?\d?)', url_or_id)
    if match:
        return match.group(1).split('v')[0] # 移除版本号
    return None


class BaseFetcher(ABC):
    source: str

    @abstractmethod
    def can_handle(self, identifier: str) -> bool:
        return is_valid_arxiv_id(identifier)

    @abstractmethod
    def fetch(self, identifier: str):
        """
        identifier: arXiv id or url
        """
        ...
