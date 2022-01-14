FROM python:3.7-slim

RUN pip install dagster

COPY bin/repo.py  /app/bin/
COPY src/ops.py  /app/src/

EXPOSE 4000

WORKDIR /app/

CMD ["dagster", "api", "grpc", "-p", "4000", "-f", "bin/repo.py" ]