import io
from fastapi import UploadFile
from pypdf import PdfReader
from ..core.logging import logger


def read_txt_or_pdf(file: UploadFile) -> str:
    logger.debug(
        f"Reading upload: name={getattr(file, 'filename', None)}, content_type={file.content_type}"
    )

    if file.content_type in ("text/plain",) or file.filename.lower().endswith(".txt"):
        raw = file.file.read()
        logger.debug(f"TXT bytes={len(raw)}")
        return raw.decode("utf-8", errors="ignore")

    if file.content_type in ("application/pdf",) or file.filename.lower().endswith(".pdf"):
        raw = file.file.read()
        logger.debug(f"PDF bytes={len(raw)}")
        data = io.BytesIO(raw)
        reader = PdfReader(data)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    try:
        return file.file.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""

