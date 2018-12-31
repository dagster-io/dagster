#! /bin/bash

docker build -f Dockerfile-2.7 -t dagster/cci-test:2.7 .
docker build -f Dockerfile-3.5 -t dagster/cci-test:3.5 .
docker build -f Dockerfile-3.6 -t dagster/cci-test:3.6 .
docker build -f Dockerfile-3.7.2 -t dagster/cci-test:3.7.2 .

docker push dagster/cci-test:2.7
docker push dagster/cci-test:3.5
docker push dagster/cci-test:3.6
