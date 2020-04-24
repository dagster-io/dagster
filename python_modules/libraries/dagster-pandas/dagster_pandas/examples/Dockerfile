FROM python:3.7.5-slim-stretch

RUN mkdir -p /tmp/results

WORKDIR /tmp/

# In a typical production deploy, use the following pattern.

# ADD requirements.txt .

# RUN pip install -r requirements.txt

# ADD dagster dagster
# ADD dagit dagit

ADD . .

RUN pip install --upgrade pip && pip install -e dagster && pip install dagit && pip install dagster-pandas && pip install dagstermill && pip install pytest

# ENTRYPOINT [ "dagit" ]
# 
# EXPOSE 3000
