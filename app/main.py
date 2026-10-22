from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

from app.db import get_conn
from app.utils import encode

app = FastAPI()


class ShortenRequest(BaseModel):
    url: HttpUrl  # rejects anything that isn't a valid http/https URL


@app.post("/shorten")
def shorten(req: ShortenRequest):
    with get_conn() as conn:
        # Reserve the next ID first, so we can compute the code before inserting
        new_id = conn.execute(
            "SELECT nextval(pg_get_serial_sequence('urls', 'id'))"
        ).fetchone()[0]
        code = encode(new_id)
        conn.execute(
            "INSERT INTO urls (id, short_code, long_url) VALUES (%s, %s, %s)",
            (new_id, code, str(req.url)),
        )
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