FROM python:3.13-slim
WORKDIR /workspace
COPY backend/requirements.txt /workspace/backend/requirements.txt
COPY packages/framesignal-metrics /workspace/packages/framesignal-metrics
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY metricsteward/backend /workspace/metricsteward/backend
COPY backend /workspace/backend
COPY reports/latest.json /workspace/reports/latest.json
RUN python -m pip wheel --no-deps ./packages/framesignal-metrics --wheel-dir /workspace/dist \
	&& python /workspace/backend/export_metricsteward.py
ENV PYTHONPATH=/workspace/metricsteward/backend
ENV METRICSTEWARD_DATABASE=/data/catalog.sqlite3
EXPOSE 8001
CMD ["uvicorn", "metricsteward.api:app", "--host", "0.0.0.0", "--port", "8001"]