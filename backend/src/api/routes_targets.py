from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends, HTTPException

from src.api.main import require_data
from src.api.models import HitRate, Target
from src.core.hit_rate import hit_rates
from src.db import queries

router = APIRouter()


@router.get("/targets", response_model=list[Target])
def targets(conn: psycopg.Connection = Depends(require_data)) -> list[dict]:
    return queries.list_targets(conn)


@router.get("/targets/{target}/hit-rates", response_model=list[HitRate])
def target_hit_rates(target: str, conn: psycopg.Connection = Depends(require_data)) -> list[dict]:
    if not queries.target_exists(conn, target):
        raise HTTPException(status_code=404, detail="Unknown target")
    return hit_rates(queries.target_designs(conn, target))
