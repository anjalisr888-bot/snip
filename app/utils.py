CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode(n: int) -> str:
    if n == 0:
        return CHARS[0]
    out = []
    while n:
        n, r = divmod(n, 62)
        out.append(CHARS[r])
    return "".join(reversed(out))


# TODO: write decode(s: str) -> int yourself