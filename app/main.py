import re
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

from app.db import get_conn
from app.utils import encode

app = FastAPI()

ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,30}$")
RESERVED = {"docs", "redoc", "openapi.json", "shorten", "favicon.ico"}


class ShortenRequest(BaseModel):
    url: HttpUrl
    alias: str | None = None


@app.post("/shorten")
def shorten(req: ShortenRequest):
    long_url = str(req.url)

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
                "INSERT INTO urls (short_code, long_url) VALUES (%s, %s) "
                "ON CONFLICT (short_code) DO NOTHING RETURNING id",
                (req.alias, long_url),
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
                "INSERT INTO urls (id, short_code, long_url) VALUES (%s, %s, %s) "
                "ON CONFLICT (short_code) DO NOTHING RETURNING id",
                (new_id, code, long_url),
            ).fetchone()
            if row is not None:
                return {"short_code": code}


@app.get("/{short_code}")
def redirect(short_code: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT long_url, expires_at FROM urls WHERE short_code = %s",
            (short_code,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Short link not found")

    long_url, expires_at = row
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Link has expired")

    return RedirectResponse(long_url, status_code=302)