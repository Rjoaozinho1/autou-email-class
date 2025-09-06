import logging
from .settings import LOG_LEVEL
from .context import request_id_var


_LEVEL = getattr(logging, LOG_LEVEL, logging.INFO)
class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Inject request_id into every record, defaulting to '-'
        record.request_id = request_id_var.get()
        return True


_FORMAT = "%(asctime)s %(levelname)s %(name)s req=%(request_id)s - %(message)s"
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(_FORMAT))
handler.addFilter(ContextFilter())

root = logging.getLogger()
root.setLevel(_LEVEL)
root.handlers = [handler]


def get_logger(name: str = "autou") -> logging.Logger:
    return logging.getLogger(name)


# Default module logger
logger = get_logger("autou")
