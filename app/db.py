import psycopg

DSN = "postgresql://postgres:pass@localhost:5432/snip"


def get_conn():
    return psycopg.connect(DSN)