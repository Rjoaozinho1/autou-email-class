import os
import io
import logging
import time
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_LEVEL = getattr(logging, LOG_LEVEL, logging.INFO)
logging.basicConfig(
    level=_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("autou")

from pypdf import PdfReader

import re
try:
    import nltk
    from nltk.corpus import stopwords
    _HAS_NLTK = True
    try:
        _ = stopwords.words("english")
    except LookupError:
        import nltk
        nltk.download("punkt")
        nltk.download("stopwords")
except Exception:
    _HAS_NLTK = False

from transformers import pipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="AutoU Email Classifier — FastAPI + HF")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CLASSIFIER_MODEL = os.getenv("HF_CLASSIFIER_MODEL")
GENERATION_MODEL = os.getenv("HF_GENERATION_MODEL")

logger.info("Starting model initialization")
logger.info(f"HF_HOME: {os.getenv('HF_HOME', '(default)')}")
logger.info(f"TRANSFORMERS_CACHE: {os.getenv('TRANSFORMERS_CACHE', '(default)')}")
logger.info(f"Classifier model: {CLASSIFIER_MODEL}")
logger.info(f"Generation model: {GENERATION_MODEL}")

_t0 = time.time()
classifier = pipeline("zero-shot-classification", model=CLASSIFIER_MODEL)
logger.info(f"Classifier pipeline ready in {time.time() - _t0:.2f}s")

_t1 = time.time()
generator = pipeline("text2text-generation", model=GENERATION_MODEL)
logger.info(f"Generator pipeline ready in {time.time() - _t1:.2f}s")

LABELS_PT = ["Produtivo", "Improdutivo"]


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


def preprocess(text: str) -> str:

    text = text or ""
    logger.debug(f"Preprocess in chars={len(text)}")

    text = re.sub(r"\s+", " ", text).strip()
    if not _HAS_NLTK:
        logger.debug("NLTK not available; returning normalized text only")
        return text
    
    langs = ["english", "portuguese"]
    sw = set()
    for lang in langs:
        try:
            sw |= set(stopwords.words(lang))
        except Exception:
            pass
    tokens = re.findall(r"\b\w+\b", text.lower())
    kept = [t for t in tokens if t not in sw]
    out = " ".join(kept)
    logger.debug(f"Preprocess out chars={len(out)}")
    return out


def classify_email(text: str) -> str:
    # Ensure overly long inputs are truncated by the tokenizer
    logger.debug(f"Classifying text chars={len(text)} labels={LABELS_PT}")
    result = classifier(text, LABELS_PT, truncation=True)
    try:
        top3 = list(zip(result.get("labels", [])[:3], result.get("scores", [])[:3]))
        logger.info(f"Classification top1={top3[0] if top3 else None} top3={top3}")
    except Exception:
        logger.exception("Failed to log classification details")
    return result["labels"][0]


def build_prompt(category: str, original_text: str) -> str:

    base_ctx = (
        "Você é um assistente de atendimento ao cliente em uma empresa financeira. "
        "Escreva uma resposta curta (em até 120 palavras), educada e objetiva. "
        "Se necessário, peça as informações mínimas para avançar. "
    )
    if category == "Produtivo":
        instr = (
            "O email é PRODUTIVO. Proponha próximos passos claros e solicite dados essenciais "
            "(ID da solicitação, CPF/CNPJ parcial, ou número do protocolo) se faltarem. "
            "Adote tom profissional e cordial, evitando jargão."
        )
    else:
        instr = (
            "O email é IMPRODUTIVO (felicitações, agradecimentos, ou assunto sem ação). "
            "Responda de forma simpática e breve, sem criar demandas."
        )

    return (
        f"{base_ctx}\n\nINSTRUÇÕES: {instr}\n\nEMAIL DO CLIENTE:\n"
        f"\"\"\"\n{original_text}\n\"\"\"\n\nRESPOSTA:"
    )


def generate_reply(category: str, original_text: str) -> str:

    prompt = build_prompt(category, original_text)
    logger.debug(
        f"Generating reply for category={category} prompt_chars={len(prompt)} max_new_tokens=180"
    )
    # Truncate the prompt to the model's max input length to avoid indexing errors
    out = generator(prompt, max_new_tokens=180, truncation=True)
    text = out[0]["generated_text"].strip()
    
    if "RESPOSTA:" in text:
        text = text.split("RESPOSTA:")[-1].strip()
    logger.info(f"Generated reply chars={len(text)}")
    return text


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/process")
async def process_email(
    file: Optional[UploadFile] = File(default=None),
    text: Optional[str] = Form(default=None),
):
    try:
        logger.info(
            f"Incoming /api/process has_file={file is not None} text_chars={len(text) if text else 0}"
        )
        content = ""
        if file is not None:
            content = read_txt_or_pdf(file)
        elif text:
            content = text

        content = (content or "").strip()
        if not content:
            return JSONResponse(status_code=400, content={"error": "Nenhum conteúdo foi enviado."})

        cleaned = preprocess(content)
        category = classify_email(cleaned)
        reply = generate_reply(category, content)

        return {"category": category, "reply": reply}
    except Exception as e:
        logger.exception("/api/process failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
        return response
    finally:
        dur_ms = (time.time() - start) * 1000
        path = request.url.path
        method = request.method
        status = (
            response.status_code if 'response' in locals() and response is not None else -1
        )
        logger.info(f"{method} {path} -> {status} in {dur_ms:.1f}ms")
