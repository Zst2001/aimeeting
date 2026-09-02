import logging
from contextvars import ContextVar


request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        return True


def configure_logging() -> None:
    """Configure concise, request-correlated application logging once."""

    root_logger = logging.getLogger()
    if any(isinstance(handler, logging.StreamHandler) for handler in root_logger.handlers):
        return

    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s"
        )
    )
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
