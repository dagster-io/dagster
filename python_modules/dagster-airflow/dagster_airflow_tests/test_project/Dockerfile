FROM python:3.7

ADD dagster dagster
ADD dagster-graphql dagster-graphql
ADD dagit dagit

RUN pip install dagster/
RUN pip install dagster-graphql/
RUN pip install dagit/

ADD requirements.txt .
RUN pip install -r requirements.txt

ADD . .

ENTRYPOINT [ "dagit", "--no-watch" ]

EXPOSE 3000
