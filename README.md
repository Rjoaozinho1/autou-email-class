# AutoU — Email Classifier (FastAPI + Hugging Face)

Uma aplicação simples que:
- Lê `.txt`/`.pdf` ou texto colado,
- Classifica como **Produtivo** ou **Improdutivo** (zero-shot),
- Gera uma **resposta automática** condizente.

## 🧱 Stack
- **Backend:** FastAPI# AutoU — Email Classifier (FastAPI + Hugging Face)

Uma aplicação simples que:
- Lê `.txt`/`.pdf` ou texto colado,
- Classifica como **Produtivo** ou **Improdutivo** (zero-shot),
- Gera uma **resposta automática** condizente.

## 🧱 Stack
- **Backend:** FastAPI
- **NLP:** Hugging Face Transformers (`facebook/bart-large-mnli` p/ classificação; `google/flan-t5-base` p/ geração)
- **Frontend:** HTML/CSS/JS (puro)

## ▶️ Rodando localmente
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export HF_HOME=.hf_cache  # (opcional) cache local
export HF_CLASSIFIER_MODEL=facebook/bart-large-mnli  # (opcional)
export HF_GENERATION_MODEL=google/flan-t5-base       # (opcional)
uvicorn app.main:app --reload --port 8000
```
Acesse: http://localhost:8000

> **Apple Silicon (M1/M2/M3)**: instale PyTorch CPU manualmente ou use modelos que não precisem de `torch` (ex.: T5 no CPU funciona, mas pode ser lento).

## 🌐 Deploy rápido (Docker)
Ver `Dockerfile` abaixo. Exemplo:
```bash
docker build -t autou-email-classifier .
docker run -p 8000:8000 --env HF_HOME=/cache --name autou autou-email-classifier
# Acesse http://localhost:8000
```

## 🔧 Notas técnicas
- **Pré-processamento:** limpeza básica + stopwords PT/EN via NLTK (opcional). O classificador usa o texto limpo; a geração recebe o texto original.
- **Zero-shot:** labels PT `Produtivo`/`Improdutivo`. Você pode trocar por labels EN se quiser.
- **Geração:** prompt curto e controlado com contexto do setor financeiro.
- **Privacidade:** considere truncar textos muito longos antes de# AutoU — Email Classifier (FastAPI + Hugging Face)

Uma aplicação simples que:
- Lê `.txt`/`.pdf` ou texto colado,
- Classifica como **Produtivo** ou **Improdutivo** (zero-shot),
- Gera uma **resposta automática** condizente.

## 🧱 Stack
- **Backend:** FastAPI
- **NLP:** Hugging Face Transformers (`facebook/bart-large-mnli` p/ classificação; `google/flan-t5-base` p/ geração)
- **Frontend:** HTML/CSS/JS (puro)

## ▶️ Rodando localmente
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export HF_HOME=.hf_cache  # (opcional) cache local
export HF_CLASSIFIER_MODEL=facebook/bart-large-mnli  # (opcional)
export HF_GENERATION_MODEL=google/flan-t5-base       # (opcional)
uvicorn app.main:app --reload --port 8000
```
Acesse: http://localhost:8000

> **Apple Silicon (M1/M2/M3)**: instale PyTorch CPU manualmente ou use modelos que não precisem de `torch` (ex.: T5 no CPU funciona, mas pode ser lento).

## 🌐 Deploy rápido (Docker)
Ver `Dockerfile` abaixo. Exemplo:
```bash
docker build -t autou-email-classifier .
docker run -p 8000:8000 --env HF_HOME=/cache --name autou autou-email-classifier
# Acesse http://localhost:8000
```

## 🔧 Notas técnicas
- **Pré-processamento:** limpeza básica + stopwords PT/EN via NLTK (opcional). O classificador usa o texto limpo; a geração recebe o texto original.
- **Zero-shot:** labels PT `Produtivo`/`Improdutivo`. Você pode trocar por labels EN se quiser.
- **Geração:** prompt curto e controlado com contexto do setor financeiro.
- **Privacidade:** considere truncar textos muito longos antes de
- **NLP:** Hugging Face Transformers (`facebook/bart-large-mnli` p/ classificação; `google/flan-t5-base` p/ geração)
- **Frontend:** HTML/CSS/JS (puro)

## ▶️ Rodando localmente
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export HF_HOME=.hf_cache  # (opcional) cache local
export HF_CLASSIFIER_MODEL=facebook/bart-large-mnli  # (opcional)
export HF_GENERATION_MODEL=google/flan-t5-base       # (opcional)
uvicorn app.main:app --reload --port 8000
```
Acesse: http://localhost:8000

> **Apple Silicon (M1/M2/M3)**: instale PyTorch CPU manualmente ou use modelos que não precisem de `torch` (ex.: T5 no CPU funciona, mas pode ser lento).

## 🌐 Deploy rápido (Docker)
Ver `Dockerfile` abaixo. Exemplo:
```bash
docker build -t autou-email-classifier .
docker run -p 8000:8000 --env HF_HOME=/cache --name autou autou-email-classifier
# Acesse http://localhost:8000
```

## 🔧 Notas técnicas
- **Pré-processamento:** limpeza básica + stopwords PT/EN via NLTK (opcional). O classificador usa o texto limpo; a geração recebe o texto original.
- **Zero-shot:** labels PT `Produtivo`/`Improdutivo`. Você pode trocar por labels EN se quiser.
- **Geração:** prompt curto e controlado com contexto do setor financeiro.
- **Privacidade:** considere truncar textos muito longos antes de enviar a modelos hospedados.

## 🚀 Extensões
- Confiança da classificação e rótulos alternativos.
- Botão de “Refinar resposta” (tom/idioma).
- Logs e métricas.
- Modelos PT-BR (ex.: NLI PT e PT-T5).
