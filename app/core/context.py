from contextvars import ContextVar


# Holds a per-request UUID for logging correlation
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

