import os
import io
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

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

classifier = pipeline("zero-shot-classification", model=CLASSIFIER_MODEL)
generator = pipeline("text2text-generation", model=GENERATION_MODEL)

LABELS_PT = ["Produtivo", "Improdutivo"]


def read_txt_or_pdf(file: UploadFile) -> str:

    if file.content_type in ("text/plain",) or file.filename.lower().endswith(".txt"):
        return file.file.read().decode("utf-8", errors="ignore")
    
    if file.content_type in ("application/pdf",) or file.filename.lower().endswith(".pdf"):
        data = io.BytesIO(file.file.read())
        reader = PdfReader(data)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    
    try:
        return file.file.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def preprocess(text: str) -> str:

    text = text or ""

    text = re.sub(r"\s+", " ", text).strip()
    if not _HAS_NLTK:
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
    return " ".join(kept)


def classify_email(text: str) -> str:
    # Ensure overly long inputs are truncated by the tokenizer
    result = classifier(text, LABELS_PT, truncation=True)
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
    # Truncate the prompt to the model's max input length to avoid indexing errors
    out = generator(prompt, max_new_tokens=180, truncation=True)
    text = out[0]["generated_text"].strip()
    
    if "RESPOSTA:" in text:
        text = text.split("RESPOSTA:")[-1].strip()
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
        return JSONResponse(status_code=500, content={"error": str(e)})
