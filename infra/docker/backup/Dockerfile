# postgres:16-alpine already ships pg_dump matching the pgvector/pgvector:pg16
# server (docker-compose.yml) — no separate client install needed.
FROM postgres:16-alpine
RUN apk add --no-cache aws-cli
COPY backup.sh /backup.sh
RUN chmod +x /backup.sh
ENTRYPOINT ["/backup.sh"]
