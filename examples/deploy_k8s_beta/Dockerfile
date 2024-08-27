ARG BASE_IMAGE

FROM "${BASE_IMAGE}"

COPY . /

# This makes sure that logs show up immediately instead of being buffered
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

RUN \
    pip install \
        dagster \
        dagster-postgres \
        dagster-k8s \


WORKDIR /example_project/

EXPOSE 80
