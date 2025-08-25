from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from starlette_context import context


def build_link_from_base_url(path: str) -> str:
    request: Request = context.get("base_url")
    return f"{request.base_url}{path}"


def build_serial_no(name: str, id: int):
    prefix = name.upper().ljust(3, "X")[:3]
    current_year = str(datetime.now(timezone.utc).year)

    return f"{prefix}-{current_year}-{str(id).zfill(4)}"


def get_current_and_total_pages(limit: int, total: Optional[int] = None, offset: Optional[int] = None):
    current_page = (offset // limit) + 1
    total_pages = (total + limit - 1) // limit

    return current_page, total_pages
