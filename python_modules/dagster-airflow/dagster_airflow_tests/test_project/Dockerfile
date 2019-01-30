FROM python:3.7

ADD requirements.txt .

RUN pip install -r requirements.txt

ADD . .

ENTRYPOINT [ "dagit", "--no-watch" ]

EXPOSE 3000
