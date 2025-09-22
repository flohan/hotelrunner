from __future__ import annotations

import logging
import uuid


class RequestIdFilter(logging.Filter):
    _installed = False

    @classmethod
    def install(cls) -> None:
        if cls._installed:
            return
        logging.getLogger().addFilter(cls())
        cls._installed = True

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def generate_request_id() -> str:
    return uuid.uuid4().hex
