"""Response models matching specs/001-binder-hit-rate-dashboard/contracts/openapi.yaml."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class Meta(BaseModel):
    snapshot_date: date
    licence: str
    credit: str
    source_file: str | None = None


class Target(BaseModel):
    slug: str
    name: str
    designs: int


class HitRate(BaseModel):
    method: str
    binders: int
    non_binders: int
    no_result: int
    labelled: int
    hit_rate: float | None
    small_sample: bool


class ScoreInfo(BaseModel):
    name: str
    designs_with_value: int


class Group(BaseModel):
    n: int
    counts: list[int]


class Distribution(BaseModel):
    score: str
    bin_edges: list[float]
    binder: Group
    non_binder: Group
    missing_count: int
    conflicting_excluded: int
    no_result_excluded: int
