# AutoU — Email Classifier (FastAPI + Groq)

Aplicação que:
- Lê `.txt`/`.pdf` ou texto colado;
- Classifica como **Produtivo** ou **Improdutivo**;
- Retorna uma **resposta automática sugerida** (pode ser vazia p/ spam/OOO).

## 🧱 Stack
- Backend: FastAPI
- LLM: Groq (cliente Python oficial, OpenAI‑compatible)
- Frontend: HTML/CSS/JS (puro)

## ▶️ Rodando localmente
Pré‑requisitos: Python 3.11+, uma chave válida do Groq (`GROQ_API_KEY`).

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Ambiente (mínimo necessário)
export GROQ_API_KEY=...                # sua chave Groq
# Opcionais (com defaults no código)
export GROQ_MODEL=llama-3.1-70b-versatile
export GENERATION_TEMPERATURE=0.7
export LOG_LEVEL=INFO

uvicorn app.main:app --reload --port 8000
```

Depois, acesse: `http://localhost:8000`.

## 🌐 Docker
```bash
docker build -t autou-email-classifier .
# Passe as variáveis de ambiente (ou use --env-file .env)
# docker run --rm -p 8000:8000 --env-file .env autou-email-classifier
docker run --rm -p 8000:8000 -e GROQ_API_KEY=... autou-email-classifier
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
- Logs: controlados por `LOG_LEVEL` (padrão `INFO`).

## 📦 Deploy
- `Dockerfile` inicia o app em `0.0.0.0:8000`.
- `Procfile` (ex.: plataformas que definem `%PORT%`).

## 🔒 Observações de privacidade
- Evite enviar dados sensíveis para provedores externos.
- Para textos muito longos, considere truncar/anonimizar.
