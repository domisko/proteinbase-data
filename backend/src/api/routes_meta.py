from __future__ import annotations

import psycopg
from fastapi import APIRouter, Depends

from src.api.main import require_data
from src.api.models import Meta
from src.db import queries

router = APIRouter()


@router.get("/meta", response_model=Meta)
def meta(conn: psycopg.Connection = Depends(require_data)) -> dict:
    return queries.latest_snapshot(conn)
