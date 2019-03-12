FROM python:3.7

RUN mkdir -p /tmp/results

WORKDIR /tmp/

# In a typical production deploy, use the following pattern.

# ADD requirements.txt .

# RUN pip install -r requirements.txt

ADD dagster dagster
ADD dagit dagit

RUN pip install dagster/
RUN pip install dagit/

ADD . .

ENTRYPOINT [ "dagit" ]

EXPOSE 3000
