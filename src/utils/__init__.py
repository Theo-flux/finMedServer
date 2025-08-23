from datetime import datetime, timezone

from fastapi import Request
from starlette_context import context


def build_link_from_base_url(path: str) -> str:
    request: Request = context.get("base_url")
    return f"{request.base_url}{path}"


def build_serial_no(name: str, id: int):
    prefix = name.upper().ljust(3, "X")[:3]
    current_year = str(datetime.now(timezone.utc).year)

    return f"{prefix}-{current_year}-{str(id).zfill(4)}"
