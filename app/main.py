import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.settings import STATIC_DIR
from .core.logging import logger
from .api.routes import router
from .core.context import request_id_var


app = FastAPI(title="AutoU Email Classifier — FastAPI")

# Static files and routes
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Assign a request id for correlation
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    token = request_id_var.set(rid)

    client_ip = request.client.host if request.client else "-"
    ua = request.headers.get("user-agent", "-")
    method = request.method
    path = request.url.path
    start = time.time()

    logger.info(f"event=request_start ip={client_ip} ua={ua} method={method} path={path}")
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response
    finally:
        dur_ms = (time.time() - start) * 1000
        status = (
            response.status_code if 'response' in locals() and response is not None else -1
        )
        logger.info(
            f"event=request_end method={method} path={path} status={status} duration_ms={dur_ms:.1f}"
        )
        # Reset context var
        request_id_var.reset(token)
