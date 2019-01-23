FROM python:3.7

ENV SLUGIFY_USES_TEXT_UNIDECODE=yes

ADD requirements.txt .

RUN pip install -r requirements.txt

ADD . .

ENTRYPOINT [ "ls" ]
# ENTRYPOINT [ "dagit" ]

EXPOSE 3000
