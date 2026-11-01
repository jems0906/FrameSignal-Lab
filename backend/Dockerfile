FROM python:3.13-slim
WORKDIR /workspace
COPY backend/requirements.txt /workspace/backend/requirements.txt
COPY packages/framesignal-metrics /workspace/packages/framesignal-metrics
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend /workspace/backend
COPY configs /workspace/configs
COPY reports/observational_extension.json reports/observational_replication.json reports/observational_robustness_stress.json reports/learned_proxy_extension.json /workspace/reports/
ENV PYTHONPATH=/workspace/backend
EXPOSE 8000
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]