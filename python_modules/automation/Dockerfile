FROM python:3.6.8-stretch

ADD requirements.txt .

RUN pip install -r requirements.txt

ADD "generate_synthetic_events.py" /

ENTRYPOINT [ "/generate_synthetic_events.py" ]
