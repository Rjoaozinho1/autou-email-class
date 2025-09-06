import requests
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from ..core.settings import TEMPLATES_DIR
from ..core.logging import logger
from ..utils.io import read_txt_or_pdf
from ..utils.text import preprocess
from ..services.classifier import classify_email


router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/")
async def index(request: Request):
    logger.debug("event=render_index")
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/api/process")
async def process_email(
    file: Optional[UploadFile] = File(default=None),
    text: Optional[str] = Form(default=None),
):
    try:
        logger.info(
            f"event=process_start has_file={file is not None} text_chars={len(text) if text else 0}"
        )
        content = ""
        if file is not None:
            content = read_txt_or_pdf(file)
        elif text:
            content = text

        content = (content or "").strip()
        if not content:
            logger.warning("event=process_validation_failed reason=empty_content")
            return JSONResponse(status_code=400, content={"error": "Nenhum conteúdo foi enviado."})

        logger.debug(f"event=preprocess_done preview={content[:200]!r}")

        category, reply = classify_email(content)

        logger.info(f"event=classified category={category}")
        logger.debug(f"event=reply_generated size={len(reply)}")

        return {"category": category, "reply": reply}

    except requests.HTTPError as http_err:
        logger.exception("event=process_failed kind=http_error")
        return JSONResponse(status_code=502, content={"error": f"Inference API error: {http_err}"})
    except Exception as e:
        logger.exception("event=process_failed kind=unhandled_exception")
        return JSONResponse(status_code=500, content={"error": str(e)})
