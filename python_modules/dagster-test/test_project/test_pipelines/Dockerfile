FROM python:3.7-slim

RUN apt-get update && apt-get install -yqq cron

RUN mkdir -p /opt/dagster/dagster_home /opt/dagster/app

RUN pip install dagit

WORKDIR /opt/dagster/app

COPY . /opt/dagster/app/
# Copy your pipeline code and repository.yaml here, e.g.:
# COPY . /opt/dagster/app/

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 3000

ENTRYPOINT ["/opt/dagster/app/entrypoint.sh"]
