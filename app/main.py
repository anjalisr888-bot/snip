import re
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, HttpUrl

from app.cache import LRUCache
from app.db import get_conn
from app.utils import encode

app = FastAPI()
cache = LRUCache(1000)

ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,30}$")
RESERVED = {"docs", "redoc", "openapi.json", "shorten", "favicon.ico", "stats"}


class ShortenRequest(BaseModel):
    url: HttpUrl
    alias: str | None = None
    expires_in_days: int | None = Field(default=None, ge=1, le=365)


@app.post("/shorten")
def shorten(req: ShortenRequest):
    long_url = str(req.url)

    expires_at = None
    if req.expires_in_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=req.expires_in_days)

    # Custom alias
    if req.alias is not None:
        if not ALIAS_PATTERN.match(req.alias):
            raise HTTPException(
                status_code=422,
                detail="Alias must be 3-30 characters: letters, numbers, - or _",
            )
        if req.alias.lower() in RESERVED:
            raise HTTPException(status_code=422, detail="This alias is reserved")

        with get_conn() as conn:
            row = conn.execute(
                "INSERT INTO urls (short_code, long_url, expires_at) VALUES (%s, %s, %s) "
                "ON CONFLICT (short_code) DO NOTHING RETURNING id",
                (req.alias, long_url, expires_at),
            ).fetchone()

        if row is None:
            raise HTTPException(status_code=409, detail="Alias already taken")
        return {"short_code": req.alias}

    # Auto-generated code: skip any code that is already taken
    with get_conn() as conn:
        while True:
            new_id = conn.execute(
                "SELECT nextval(pg_get_serial_sequence('urls', 'id'))"
            ).fetchone()[0]
            code = encode(new_id)
            row = conn.execute(
                "INSERT INTO urls (id, short_code, long_url, expires_at) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (short_code) DO NOTHING RETURNING id",
                (new_id, code, long_url, expires_at),
            ).fetchone()
            if row is not None:
                return {"short_code": code}


@app.get("/stats/{short_code}")
def stats(short_code: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, long_url FROM urls WHERE short_code = %s", (short_code,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Short link not found")
        url_id, long_url = row

        total = conn.execute(
            "SELECT count(*) FROM clicks WHERE url_id = %s", (url_id,)
        ).fetchone()[0]

        per_day = conn.execute(
            "SELECT clicked_at::date AS day, count(*) FROM clicks "
            "WHERE url_id = %s GROUP BY day ORDER BY day",
            (url_id,),
        ).fetchall()

        referrers = conn.execute(
            "SELECT COALESCE(referrer, 'direct') AS ref, count(*) FROM clicks "
            "WHERE url_id = %s GROUP BY ref ORDER BY count(*) DESC LIMIT 10",
            (url_id,),
        ).fetchall()

    return {
        "short_code": short_code,
        "long_url": long_url,
        "total_clicks": total,
        "clicks_per_day": [{"date": str(d), "clicks": c} for d, c in per_day],
        "top_referrers": [{"referrer": r, "clicks": c} for r, c in referrers],
    }


@app.get("/{short_code}")
def redirect(short_code: str, request: Request):
    entry = cache.get(short_code)

    with get_conn() as conn:
        if entry is None:
            row = conn.execute(
                "SELECT id, long_url, expires_at FROM urls WHERE short_code = %s",
                (short_code,),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Short link not found")
            entry = (row[0], row[1], row[2])
            cache.put(short_code, entry)

        url_id, long_url, expires_at = entry
        if expires_at and expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Link has expired")

        conn.execute(
            "INSERT INTO clicks (url_id, referrer, user_agent) VALUES (%s, %s, %s)",
            (
                url_id,
                request.headers.get("referer"),
                request.headers.get("user-agent"),
            ),
        )

    return RedirectResponse(long_url, status_code=302)