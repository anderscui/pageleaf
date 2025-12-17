# coding=utf-8
from pageleaf.fetchers.base import is_valid_arxiv_id, extract_arxiv_id


def test_is_valid_arxiv_id():
    test_cases = [
        # 有效的新格式
        ("2301.12345", True),
        ("2301.12345v1", True),
        ("2301.12345v10", True),
        ("1234.56789", True),
        ("0704.0001", True),  # 第一篇新格式论文

        # 有效的旧格式
        ("cs/0703001", True),
        ("math.AG/0703001", True),
        ("hep-th/9901001", True),
        ("astro-ph/0703001v2", True),

        # 无效格式
        ("", False),
        ("abc", False),
        ("2301.123", False),  # 编号太短
        ("2301.123456", False),  # 编号太长
        ("23011.2345", False),  # 年月格式错误
        ("2301-12345", False),  # 分隔符错误
        ("cs/070300", False),  # 旧格式编号位数错误
        ("CS/0703001", False),  # 旧格式 archive 大写
        ("2301.12345v", False),  # version 号缺失
        ("v1.2301.12345", False),  # version 位置错误
    ]
    for arxiv_id, expected in test_cases:
        assert is_valid_arxiv_id(arxiv_id) == expected


def test_extract_arxiv_id():
    cases = [
        ("2301.12345", "2301.12345"),
        ("2301.12345v2", "2301.12345"),
        ("2301.12345v11", "2301.12345"),

        # valid urls
        ('https://arxiv.org/abs/2501.01234', '2501.01234'),
        ('https://arxiv.org/pdf/2309.06180', '2309.06180'),
        ('https://arxiv.org/pdf/2309.06180/', '2309.06180'),

        ("", None),
        ("abc", None),
        ("2301.123", None),
        ("2301.123456", None)
    ]

    for arxiv_id, expected in cases:
        assert extract_arxiv_id(arxiv_id) == expected
