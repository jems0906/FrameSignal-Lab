FROM python:3.13-slim
WORKDIR /workspace
COPY backend/requirements.txt /workspace/backend/requirements.txt
COPY packages/framesignal-metrics /workspace/packages/framesignal-metrics
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY metricsteward/backend /workspace/metricsteward/backend
COPY reports/latest.json reports/metricsteward_handoff.json /workspace/reports/
COPY dist/framesignal_metrics-1.0.0-py3-none-any.whl /workspace/dist/
ENV PYTHONPATH=/workspace/metricsteward/backend
ENV METRICSTEWARD_DATABASE=/data/catalog.sqlite3
EXPOSE 8001
CMD ["uvicorn", "metricsteward.api:app", "--host", "0.0.0.0", "--port", "8001"]