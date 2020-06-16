FROM python:3.7-slim

# Cron is required to use scheduling in Dagster
RUN apt-get update && apt-get install -yqq cron

RUN mkdir -p /opt/dagster/dagster_home /opt/dagster/app

RUN pip install dagit

# Copy your pipeline code and entrypoint.sh to /opt/dagster/app
COPY pipelines.py entrypoint.sh /opt/dagster/app/

# Copy dagster instance YAML to $DAGSTER_HOME
COPY dagster.yaml /opt/dagster/dagster_home/

WORKDIR /opt/dagster/app

RUN chmod +x entrypoint.sh

EXPOSE 3000

ENTRYPOINT ["/opt/dagster/app/entrypoint.sh"]
