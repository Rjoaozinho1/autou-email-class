import os
import io
import logging
import time
import json
import re
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from pypdf import PdfReader
import requests
from groq import Groq


load_dotenv()


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_LEVEL = getattr(logging, LOG_LEVEL, logging.INFO)
logging.basicConfig(
    level=_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("autou")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="AutoU Email Classifier — FastAPI")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

GENERATION_TEMPERATURE = float(os.getenv("GENERATION_TEMPERATURE", "0.7"))
CLASSIFICATION_TEMPERATURE = 0.0

LABELS_PT = ["Produtivo", "Improdutivo"]

STOP_PT = {
    "de", "da", "do", "dos", "das", "o", "a", "os", "as", "um", "uma", "para", "por",
    "em", "e", "ou", "que", "com", "no", "na", "nos", "nas"
}
STOP_EN = {
    "the", "a", "an", "in", "on", "at", "of", "for", "and", "or", "to", "is", "are",
    "be", "was", "were", "this", "that"
}
STOP = STOP_PT | STOP_EN


def preprocess(text: str) -> str:

    logger.debug(f"Preprocess in chars={len(text) if text else 0}")

    text = re.sub(r"\s+", " ", (text or "")).strip()
    tokens = re.findall(r"\b\w+\b", text.lower())
    kept = [t for t in tokens if t not in STOP]
    out = " ".join(kept) if kept else text
    logger.debug(f"Preprocess out chars={len(out)}")

    return out


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
    

def _groq_chat(messages: List[dict], temperature: float = 0.0, max_tokens: int = 128) -> str:
    """Call Groq using the official groq Python client (non-stream)."""

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in environment")

    client = Groq(api_key=GROQ_API_KEY)

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_tokens,
        top_p=1,
        stream=False,
        stop=None,
    )

    try:
        return (completion.choices[0].message.content or "").strip()
    except Exception:
        try:
            return str(completion["choices"][0]["message"]["content"]).strip()
        except Exception:
            return ""


def classify_email(text: str) -> tuple[str, str]:
    """
    Usa Groq com um prompt de classificação. Pede resposta estrita JSON para robustez.
    """

    email_excerpt = text
    system = """
    Você é um classificador rigoroso de emails corporativos em pt-BR para uma empresa do setor financeiro. Sua missão é, para CADA email recebido, (1) classificar como "Produtivo" ou "Improdutivo"; (2) sugerir uma resposta automática sucinta em pt-BR de acordo com a classificacao; (3) retornar TUDO em JSON válido, sem qualquer texto extra.

    # Informacoes
    Esses emails podem ser mensagens solicitando um status atual sobre uma requisição em andamento, compartilhando algum arquivo ou até mesmo mensagens improdutivas, como desejo de feliz natal ou perguntas não relevantes. 

    # Classificacao
        - Produtivo: requer ação/resposta específica do time (ex.: solicitação de suporte, pedido de status/atualização de caso, dúvida técnica, envio/solicitação de documentos relevantes, alinhamento operacional, ajuste de acesso/credencial, incidentes, cobrança contestada, compliance/KYC), classifique como Produtivo.

        - Improdutivo: não requer ação imediata (ex.: felicitações/agradecimentos, mensagens genéricas, “FYI” sem pedido, ausência, ooo/marketing não solicitado, spam). Se o conteúdo pede ação mas já foi resolvido no próprio email (sem pendência) e não solicita confirmação, classifique como Improdutivo.

    # Regras de decisão
    1) **Phishing/Spam suspeito?** Se forte indício (links estranhos, anexos executáveis, pedido de credenciais): label=Improdutivo.
    2) **OOO/ausência automática?** (palavras como "fora do escritório", "volto em", “automatic reply”): label=Improdutivo.
    3) **Existe pedido claro, prazo, pergunta objetiva ou referência a ticket/caso?**: label=Produtivo.
    4) **Apenas cortesia/agradecimento/felicitação sem pedido?**: label=Improdutivo.
    5) **Compartilha documentos relevantes a um processo em andamento?**: label=Produtivo
    6) **Conteúdo ambíguo:** Se há chance razoável de que o time precise agir (ex.: “segue em anexo o relatório deste mês”): label=Produtivo.

    # Sugestão de resposta automática (pt-BR, tom profissional, 80-180 palavras)
    - Para Produtivo: reconheça o pedido, cite o ID/caso se houver, diga próximo passo e prazo padrão (ou o prazo detectado), peça o que faltar (documento, print, número do caso). Evite promessas fortes; prefira "estamos analisando".
    - Para Improdutivo:
    • greeting/thank_you: resposta curta e cordial (≤40 palavras).
    • ooo/spam_phishing/newsletter_marketing: sugerir_reply vazio.
    - Nunca inclua links suspeitos. Não peça dados sensíveis desnecessários.

    # Formato de saída (obrigatório, JSON estrito)
    Retorne **apenas** um objeto JSON com as chaves:
    {
        "label": "Produtivo" | "Improdutivo",
        "suggested_reply": "Resposta sobre o email em pt-BR"
    }

    # Observâncias
    - Respeite LGPD: não exponha dados sensíveis além do mínimo necessário.
    - Nunca faça suposições inventadas; se não há dado, deixe o campo vazio/omitido conforme o esquema.
    - Nunca imprima texto fora do JSON. **Sem** markdown, sem comentários.

    # Exemplos (few-shot)

    [Exemplo 1 — Produtivo/status_update]
    Email:
    "Bom dia, poderiam informar o status do chamado CASE#54821 sobre a integração com o ERP Y? Precisamos de um posicionamento até 06/09."
    Saída esperada:
    {
        "label":"Produtivo",
        "suggested_reply":"Olá! Identificamos o chamado CASE#54821 e estamos analisando a integração com o ERP Y. Retornaremos com atualização até 06/09. Se possível, envie prints de erro ou logs recentes para acelerarmos. Permanecemos à disposição."
    }

    [Exemplo 2 — Produtivo/document_share]
    Email:
    "Segue em anexo o relatório de conformidade solicitado para o dossiê do cliente 123. Precisando de algo mais, avisem."
    Saída esperada:
    {
        "label":"Produtivo",
        "suggested_reply":"Obrigado pelo envio do relatório de conformidade do cliente 123. Vamos validar o documento e retornamos caso falte alguma peça. Se houver versão atualizada ou comprovantes adicionais, pode nos encaminhar."
    }

    [Exemplo 3 — Improdutivo/greeting]
    Email:
    "Feliz Natal a toda a equipe! Muito sucesso!"
    Saída esperada:
    {
        "label":"Improdutivo",
        "suggested_reply":"Agradecemos a mensagem e desejamos ótimas festas!"
    }

    [Exemplo 5 — Improdutivo/spam_phishing]
    Email:
    "Atualize sua senha do banco aqui: http://banco-seguro-login.xyz anexamos arquivo .exe para facilitar."
    Saída esperada:
    {
        "label":"Improdutivo",
        "suggested_reply":""
    }

    [Fim dos exemplos]

    Lembrete final: sua resposta deve ser APENAS o JSON, válido e bem formatado, conforme o esquema acima.
    """

    user = f"EMAIL:\n\"\"\"\n{email_excerpt}\n\"\"\""

    out = _groq_chat(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=CLASSIFICATION_TEMPERATURE,
        max_tokens=128,
    )

    label = None
    reply = None

    try:

        data = json.loads(out)
        label = str(data.get("label", "")).strip()
        reply = str(data.get("suggested_reply","")).strip()

    except Exception:

        m = re.search(r'"label"\s*:\s*"(?P<label>[^"]+)"', out, re.IGNORECASE)
        r = re.search(r'"suggested_reply"\s*:\s*"(?P<reply>[^"]+)"', out, re.IGNORECASE)

        if m and r:
            label = m.group("label").strip()
            reply = r.group("suggested_reply").strip()
        elif m:
            label = m.group("label").strip()
        elif r:
            reply = r.group("suggested_reply").strip()
        else:
            label = out.strip()
            reply = out.strip()

    label_norm = label.lower()

    if "produtivo" in label_norm:
        final = "Produtivo"
    elif "improdutivo" in label_norm:
        final = "Improdutivo"
    else:
        final = "Improdutivo"

    logger.info(f"classification -> raw='{out}' | label='{final}'")

    return final, reply


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

        logger.info(f"Content chars after preprocess: {cleaned[:200]}")

        category, reply = classify_email(cleaned)

        logger.info(f"Email classified as: {category}")
        logger.info(f"Generated reply chars: {reply}")

        return {"category": category, "reply": reply}

    except requests.HTTPError as http_err:

        logger.exception("/api/process failed (HTTP)")
        return JSONResponse(status_code=502, content={"error": f"Inference API error: {http_err}"})
    
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
