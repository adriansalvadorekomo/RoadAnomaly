# RoadAnomaly landing page: built with Node, served as static files by nginx (port 80 in the container).
# Build from the repository root:  docker compose -f deployment/docker-compose.yml build landing
# The page reads reports/results/*.json (tracked) and the photographs / score maps in deployment/landing/public,
# which `mise run landing:data` generates from the trained models (git-ignored, so run it once before building).
FROM node:22-alpine AS build
WORKDIR /repo
COPY deployment/landing/package.json deployment/landing/package-lock.json deployment/landing/
RUN npm --prefix deployment/landing ci
COPY deployment/landing deployment/landing
COPY reports/results reports/results
# the links of the page; override at build time for another host:  --build-arg PUBLIC_DEMO_URL=https://...
ARG PUBLIC_DEMO_URL=http://localhost:8501
ARG PUBLIC_API_URL=http://localhost:8000/docs
ENV PUBLIC_DEMO_URL=$PUBLIC_DEMO_URL PUBLIC_API_URL=$PUBLIC_API_URL
RUN test -d deployment/landing/public/demo || (echo "deployment/landing/public/demo is missing: run 'mise run landing:data' first" >&2; exit 1)
RUN npm --prefix deployment/landing run build

FROM nginx:1.27-alpine
COPY deployment/landing/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /repo/deployment/landing/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
