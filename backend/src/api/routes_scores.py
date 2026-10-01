from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.main import require_data
from src.api.models import Distribution, ScoreInfo
from src.core.distributions import distribution, select_scores
from src.db import queries

router = APIRouter()


@router.get("/targets/{target}/scores", response_model=list[ScoreInfo])
def scores(target: str, conn: psycopg.Connection = Depends(require_data)) -> list[dict]:
    if not queries.target_exists(conn, target):
        raise HTTPException(status_code=404, detail="Unknown target")
    return queries.target_scores(conn, target)


@router.get("/targets/{target}/scores/{score}/distribution", response_model=Distribution)
def score_distribution(
    target: str,
    score: str,
    bins: int = Query(20, ge=2, le=100),
    conn: psycopg.Connection = Depends(require_data),
) -> dict:
    if not queries.target_exists(conn, target):
        raise HTTPException(status_code=404, detail="Unknown target")
    raw = queries.metric_values(conn, target, score)
    if raw.is_empty():
        raise HTTPException(status_code=404, detail="Unknown score for this target")
    designs = queries.target_designs(conn, target).select("design_id", "outcome")
    return distribution(designs, select_scores(raw, target), score, bins)
