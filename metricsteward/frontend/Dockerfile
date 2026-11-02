FROM node:22-alpine AS build
WORKDIR /app
ARG VITE_FRAMESIGNAL_URL=http://localhost:8080
ENV VITE_FRAMESIGNAL_URL=$VITE_FRAMESIGNAL_URL
COPY metricsteward/frontend/package*.json ./
RUN npm ci
COPY metricsteward/frontend/ ./
RUN npm run build
FROM nginx:1.27-alpine
COPY metricsteward/frontend/nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
ENV METRICSTEWARD_API_UPSTREAM=http://metricsteward-backend:8001
ENV NGINX_ENVSUBST_FILTER=^(METRICSTEWARD_API_UPSTREAM)$
EXPOSE 80