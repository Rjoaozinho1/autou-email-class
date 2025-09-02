web: pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*' --workers 1

docker: docker build -t autou-email-classifier . && docker run --rm -p $PORT:$PORT -e HF_CLASSIFIER_MODEL=$HF_CLASSIFIER_MODEL -e HF_GENERATION_MODEL=$HF_GENERATION_MODEL autou-email-classifier