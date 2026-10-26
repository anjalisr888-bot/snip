CREATE TABLE urls (
    id          BIGSERIAL PRIMARY KEY,
    short_code  VARCHAR(20) UNIQUE NOT NULL,
    long_url    TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now(),
    expires_at  TIMESTAMPTZ
);
CREATE TABLE clicks (
    id          BIGSERIAL PRIMARY KEY,
    url_id      BIGINT NOT NULL REFERENCES urls(id),
    clicked_at  TIMESTAMPTZ DEFAULT now(),
    referrer    TEXT,
    user_agent  TEXT
);

CREATE INDEX idx_clicks_url_id ON clicks(url_id);