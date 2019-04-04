#! /bin/bash

docker build -f Dockerfile-2.7.16 -t dagster/cci-test:2.7.16 .
docker build -f Dockerfile-3.5.7 -t dagster/cci-test:3.5.7 .
docker build -f Dockerfile-3.6.8 -t dagster/cci-test:3.6.8 .
docker build -f Dockerfile-3.7.3 -t dagster/cci-test:3.7.3 .

docker push dagster/cci-test:2.7.16
docker push dagster/cci-test:3.5.7
docker push dagster/cci-test:3.6.8
docker push dagster/cci-test:3.7.3
