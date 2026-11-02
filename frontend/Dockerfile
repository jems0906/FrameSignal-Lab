FROM node:22-alpine AS build
WORKDIR /app
ARG VITE_METRICSTEWARD_URL=http://localhost:8082
ENV VITE_METRICSTEWARD_URL=$VITE_METRICSTEWARD_URL
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
FROM nginx:1.27-alpine
COPY frontend/nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
ENV FRAMESIGNAL_API_UPSTREAM=http://backend:8000
ENV NGINX_ENVSUBST_FILTER=^(FRAMESIGNAL_API_UPSTREAM)$
EXPOSE 80