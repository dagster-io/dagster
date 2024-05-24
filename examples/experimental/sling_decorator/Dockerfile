FROM postgres:15

ENV POSTGRES_DB=finance
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

COPY init_finance_db.sql /docker-entrypoint-initdb.d/
