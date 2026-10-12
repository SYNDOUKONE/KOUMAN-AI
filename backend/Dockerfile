# Image CPU, suffisante pour les stubs et pour tester le vrai modèle lentement.
# Pour le GPU : partir d'une image nvidia/cuda et installer torch cu128 (voir README).
FROM python:3.11-slim
WORKDIR /srv
COPY requirements.txt requirements-model.txt ./
ARG WITH_MODEL=false
RUN pip install --no-cache-dir -r requirements.txt \
 && if [ "$WITH_MODEL" = "true" ]; then \
      pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
      && pip install --no-cache-dir -r requirements-model.txt; fi
COPY app ./app
COPY config ./config
COPY scripts ./scripts
# Les poids du modèle ne sont JAMAIS copiés dans l'image : monter un volume.
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
