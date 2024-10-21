---
title: "Deploying with Docker Compose"
description: A guide to deploying Dagster with Docker Compose.
---

This guide provides instructions for deploying Dagster using Docker Compose. This is useful when you want to, for example, deploy Dagster on an AWS EC2 host. A typical Dagster Docker deployment includes a several long-running containers: one for the webserver, one for the daemon, and one for each code location. It also typically executes each run in its own container.

<details>
  <summary>Prerequisites</summary>
- Familiarity with Docker and Docker Compose
- Familiarity with `dagster.yaml` instance configuration
- Familiarity with `workspace.yaml` code location configuration
</details>


## Define a Docker image for the Dagster webserver and daemon

The Dagster webserver and daemon are the two _host processes_ in a Dagster deployment. They typically each run in their own container, using the same Docker image. This image contains Dagster packages and configuration, but no user code.

To build this Docker image, use a Dockerfile like the following, with a name like `Dockerfile_dagster`:

```dockerfile
FROM python:3.10-slim

RUN pip install \
    dagster \
    dagster-graphql \
    dagster-webserver \
    dagster-postgres \   # Database for Dagster storage
    dagster-docker       # Enables the Docker run launcher

# Set $DAGSTER_HOME and copy dagster.yaml and workspace.yaml there
ENV DAGSTER_HOME=/opt/dagster/dagster_home/

RUN mkdir -p $DAGSTER_HOME

COPY dagster.yaml workspace.yaml $DAGSTER_HOME

WORKDIR $DAGSTER_HOME
```

Additionally, the following files should be in the same directory as the Docker file:
- A `workspace.yaml` to tell the webserver and daemon the location of the code servers
- A `dagster.yaml` to configure the Dagster instance

## Define a Docker image for each code location

Each code location typically has its own Docker image, and that image is also used for runs launched for that code location.

To build a Docker image for a code location, use a Dockerfile like the following, with a name like `Dockerfile_code_location_1`:

```dockerfile
FROM python:3.10-slim

RUN pip install \
    dagster \
    dagster-postgres \
    dagster-docker

# Add code location code
WORKDIR /opt/dagster/app
COPY directory/with/your/code/ /opt/dagster/app

# Run dagster code server on port 4000
EXPOSE 4000

# CMD allows this to be overridden from run launchers or executors to execute runs and steps
CMD ["dagster", "code-server", "start", "-h", "0.0.0.0", "-p", "4000", "-f", "definitions.py"]
```

## Write a Docker Compose file

The following `docker-compose.yaml` defines how to run the webserver container, daemon container, code location containers, and database container:

```yaml title="docker-compose.yaml"
version: "3.7"

services:
  # This service runs the postgres DB used by dagster for run storage, schedule storage,
  # and event log storage.
  docker_postgresql:
    image: postgres:11
    container_name: docker_postgresql
    environment:
      POSTGRES_USER: "postgres_user"
      POSTGRES_PASSWORD: "postgres_password"
      POSTGRES_DB: "postgres_db"
    networks:
      - docker_network

  # This service runs the code server that loads your user code.
  docker_code_location_1:
    build:
      context: .
      dockerfile: ./Dockerfile_code_location_1
    container_name: docker_code_location_1
    image: docker_user_code_image
    restart: always
    environment:
      DAGSTER_POSTGRES_USER: "postgres_user"
      DAGSTER_POSTGRES_PASSWORD: "postgres_password"
      DAGSTER_POSTGRES_DB: "postgres_db"
      DAGSTER_CURRENT_IMAGE: "docker_user_code_image"
    networks:
      - docker_network

  # This service runs dagster-webserver.
  docker_webserver:
    build:
      context: .
      dockerfile: ./Dockerfile_dagster
    entrypoint:
      - dagster-webserver
      - -h
      - "0.0.0.0"
      - -p
      - "3000"
      - -w
      - workspace.yaml
    container_name: docker_webserver
    expose:
      - "3000"
    ports:
      - "3000:3000"
    environment:
      DAGSTER_POSTGRES_USER: "postgres_user"
      DAGSTER_POSTGRES_PASSWORD: "postgres_password"
      DAGSTER_POSTGRES_DB: "postgres_db"
    volumes: # Make docker client accessible so we can terminate containers from the webserver
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/io_manager_storage:/tmp/io_manager_storage
    networks:
      - docker_network
    depends_on:
      - docker_postgresql
      - docker_code_location_1

  # This service runs the dagster-daemon process, which is responsible for taking runs
  # off of the queue and launching them, as well as creating runs from schedules or sensors.
  docker_daemon:
    build:
      context: .
      dockerfile: ./Dockerfile_dagster
    entrypoint:
      - dagster-daemon
      - run
    container_name: docker_daemon
    restart: on-failure
    environment:
      DAGSTER_POSTGRES_USER: "postgres_user"
      DAGSTER_POSTGRES_PASSWORD: "postgres_password"
      DAGSTER_POSTGRES_DB: "postgres_db"
    volumes: # Make docker client accessible so we can launch containers using host docker
      - /var/run/docker.sock:/var/run/docker.sock
      - /tmp/io_manager_storage:/tmp/io_manager_storage
    networks:
      - docker_network
    depends_on:
      - docker_postgresql
      - docker_code_location_1

networks:
  docker_network:
    driver: bridge
    name: docker_network
```

## Start your deployment

To start the deployment, run:

```shell
docker compose up
```
