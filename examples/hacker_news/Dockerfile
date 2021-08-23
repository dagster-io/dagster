FROM python:3.8.7-slim

# Install an editable copy of the hacker_news package (using the local setup.py)

ADD hacker_news /hacker_news
ADD hacker_news_dbt /hacker_news_dbt
ADD setup.py .
RUN pip install -e .

# Ensure example can run when using either DockerRunLauncher or K8sRunLauncher
RUN pip install dagster-docker dagster-k8s

# Install Java 11 (for pyspark 3) and confirm that it works
# Deal with slim variants not having man page directories (which causes "update-alternatives" to fail)
RUN mkdir -p /usr/share/man/man1 /usr/share/man/man2 && \
    apt-get update -yqq \
    && apt-get upgrade -yqq && \
    apt-get install -yqq openjdk-11-jdk-headless \
    openjdk-11-jre-headless && \
    java -version