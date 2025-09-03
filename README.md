# AutoU — Email Classifier (FastAPI + Hugging Face)

Uma aplicação simples que:
- Lê `.txt`/`.pdf` ou texto colado,
- Classifica como **Produtivo** ou **Improdutivo** (zero-shot),
- Gera uma **resposta automática** condizente.

## 🧱 Stack
- **Backend:** FastAPI
- **NLP:**
  - Classificação: Hugging Face Transformers (`facebook/bart-large-mnli`)
  - Geração: configurável — Hugging Face (padrão) ou provedor externo (Groq / NVIDIA NIM)
- **Frontend:** HTML/CSS/JS (puro)

## ▶️ Rodando localmente
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Classificador (HF)
export HF_CLASSIFIER_MODEL=facebook/bart-large-mnli

# Geração (escolha UMA das opções abaixo)

# 1) Hugging Face (padrão)
export GENERATION_PROVIDER=hf
export HF_GENERATION_MODEL=google/flan-t5-base

# 2) Groq (OpenAI-compatible)
# export GENERATION_PROVIDER=groq
# export GROQ_API_KEY=...  # defina sua chave
# export GROQ_MODEL=llama-3.1-70b-versatile

# 3) NVIDIA NIM (OpenAI-compatible)
# export GENERATION_PROVIDER=nvidia
# export NIM_API_KEY=...   # ou NVIDIA_API_KEY
# export NIM_MODEL=meta/llama-3.1-70b-instruct

uvicorn app.main:app --reload --port 8000
```

## 🌐 Deploy rápido (Docker)
Ver `Dockerfile` abaixo. Exemplo:
```bash
docker build -t autou-email-classifier .
docker run --rm -p 8000:8000 --env-file .env autou-email-classifier
```

## Acesse: 'http://localhost:8000'

## 🔧 Notas técnicas
- **Pré-processamento:** limpeza básica + stopwords PT/EN via NLTK (opcional). O classificador usa o texto limpo; a geração recebe o texto original.
- **Zero-shot:** labels PT `Produtivo`/`Improdutivo`. Você pode trocar por labels EN se quiser.
- **Geração:** prompt curto e controlado com contexto do setor financeiro. Para Groq/NIM usamos a rota OpenAI-compatible `/v1/chat/completions`.
- **Privacidade:** considere truncar textos muito longos antes de
  enviar a provedores externos.
