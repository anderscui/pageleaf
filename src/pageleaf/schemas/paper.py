# coding=utf-8
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class Tier(str, Enum):
    """收录优先级/质量层级"""
    P0 = "p0"  # 顶会获奖论文
    P1 = "p1"  # 社区高热度论文
    P2 = "p2"  # 用户手动确定的重要论文


class ExternalIdentifiers(BaseModel):
    arxiv: str | None = None
    doi: str | None = None
    acl: str | None = None


class Metadata(BaseModel):
    title: str
    authors: list[str] = []
    year: int | None  # 2025
    publish_date: datetime | None = None
    venue: str | None  # ACL, NeurIPS, arXiv, etc.
    paper_type: str | None  # conference, journal, preprint
    source: str  # arxiv / huggingface / manual


class Content(BaseModel):
    abstract: str | None
    outline: str | None
    keywords: list[str] = []
    tags: list[str] = []
    resources: list[str] = []  # for repo, dataset or demo. 用户可能会编辑


class PaperAnalysis(BaseModel):
    contribution: str | None = Field(None, description='主要贡献和解决的问题')
    novelty: str | None = Field(None, description='新颖性分析（如与先前 SOTA 的对比）')
    limitations: str | None = Field(None, description='局限性或待改进之处')
    assumptions: str | None = Field(None, description="核心理论假设或实验前提")

    rigor_score: int | None = Field(None, description="1-5 评分，硬核/扎实程度", ge=1, le=5)
    relevance: str | None = Field(None, description="对用户关注方向的相关性分析")


class Paper(BaseModel):
    id: UUID
    identifiers: ExternalIdentifiers
    metadata: Metadata
    content: Content
    analysis: PaperAnalysis


class PaperRelations(BaseModel):
    """论文之间的关系，这里的id都使用内部 id。"""

    cites: list[UUID] = []
    cited_by: list[UUID] = []
    based_on: list[UUID] = []
    related: list[UUID] = []


class PaperEngagement(BaseModel):
    tier: Tier = Field(..., description='收录优先级 (P0/P1/P2)')
    entry_reason: str | None = Field(None, description='系统自动或用户手动指定的入库原因')
    context_at_entry: str | None = Field(None, description='入库时的情境或思考（如：最近常被引用）')

    rating: int | None = Field(None, description='用户主观评分 (1-5星)', ge=1, le=5)
    starred: bool = Field(False, description="是否被用户标星")
    labels: list[str] = Field(default_factory=list, description="用户自定义标签，用于分类和检索")
    notes: list[str] = Field(default_factory=list, description="用户笔记的内部ID列表 (未来可关联)")


class PaperEntry(BaseModel):
    paper: Paper
    paper_relations: PaperRelations | None = None
    engagement: PaperEngagement | None = None


if __name__ == '__main__':
    pass
