# AutoU — Email Classifier

Classificador de emails com FastAPI e Groq, separando responsabilidades em módulos claros (API, serviços, utilitários e core). Permite enviar texto ou arquivos `.txt/.pdf`, classifica o conteúdo como Produtivo/Improdutivo e sugere uma resposta automática em pt‑BR.

Aplicação que:
- Lê `.txt`/`.pdf` ou texto colado;
- Classifica como **Produtivo** ou **Improdutivo**;
- Retorna uma **resposta automática sugerida** (pode ser vazia p/ spam/OOO).

## 🧱 Tecnologias
- Backend: FastAPI (Starlette) + Uvicorn
- Templates: Jinja2 (páginas em `app/templates`)
- Estáticos: HTML/CSS/JS puro (`app/static`)
- LLM: Groq (SDK Python oficial)
- PDFs: pypdf (extração de texto)
- Uploads: python‑multipart (form/multipart)
- Config: python‑dotenv (`.env`)
- HTTP: requests (erros tratados)
- Logs: logging padrão com Request ID e contexto

Estrutura principal:
- `app/main.py`: inicialização do FastAPI, CORS, estáticos, middlewares e roteador.
- `app/api/routes.py`: rotas (`/` e `/api/process`).
- `app/services/`: chamadas ao Groq e classificadores.
- `app/utils/`: leitura de arquivos e pré‑processamento de texto.
- `app/core/`: configurações, logging e contexto (Request ID).

## ▶️ Rodando localmente (Python)
Pré‑requisitos: Python 3.11+ (Docker usa 3.11; `.python-version` usa 3.13 para dev), e uma chave válida do Groq (`GROQ_API_KEY`).

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Ambiente (mínimo necessário)
export GROQ_API_KEY=...                # sua chave Groq
# Opcionais (com defaults no código)
export GROQ_MODEL=llama-3.1-70b-versatile
export GENERATION_TEMPERATURE=0.7
export LOG_LEVEL=INFO

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Depois, acesse: `http://localhost:8000`.

## 🌐 Docker
```bash
docker build -t autou-email-classifier .
# Passe as variáveis de ambiente (ou use --env-file .env)
# docker run --rm -p 8000:8000 --env-file .env autou-email-classifier
docker run --rm -p 8000:8000 -e GROQ_API_KEY=... autou-email-classifier

Logs padrão saem no stdout do container. Ajuste `LOG_LEVEL` para `DEBUG` se precisar inspecionar mais detalhes.
```

## API
- `GET /`: página web simples para upload/cola de texto.
- `POST /api/process` (multipart/form-data): aceita `file` (.txt/.pdf) ou `text`.
  - Resposta: `{ "category": "Produtivo|Improdutivo", "reply": "<texto|vazio>" }`.

## ⚙️ Comportamento
- Pré‑processamento: limpeza de espaços e remoção de stopwords simples (PT/EN) antes da classificação.
- Classificação: prompt estruturado via Groq, saída JSON estrita; rótulos em PT‑BR `Produtivo`/`Improdutivo`.
- Resposta sugerida: curta e profissional; para spam/phishing/OOO pode vir vazia.
- Suporte de arquivos: `.txt` e `.pdf`.
- Logs: controlados por `LOG_LEVEL` (padrão `INFO`), com `req=<request_id>` para correlação; eventos seguem padrão `event=<nome> key=value`.

Exemplos de eventos e headers:
- `event=request_start method=POST path=/api/process ...`
- `event=process_start has_file=true text_chars=0`
- `event=classified category=Produtivo`
- Header de resposta: `X-Request-ID` para rastrear o mesmo id no cliente.

## 📦 Deploy
- `Dockerfile` inicia o app em `0.0.0.0:8000`.
- `Procfile` (ex.: plataformas que definem `%PORT%`).

## 🔒 Observações de privacidade
- Evite enviar dados sensíveis para provedores externos.
- Para textos muito longos, considere truncar/anonimizar.
