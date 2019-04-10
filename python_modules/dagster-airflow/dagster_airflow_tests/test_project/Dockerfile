FROM python:3.7

ADD dagster dagster
ADD dagster-graphql dagster-graphql

RUN pip install dagster/
RUN pip install dagster-graphql/

ADD requirements.txt .
RUN pip install -r requirements.txt

ADD . .

ENTRYPOINT [ "dagster-graphql" ]
