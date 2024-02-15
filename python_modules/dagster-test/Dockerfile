ARG BASE_IMAGE
ARG PYTHON_VERSION

FROM "${BASE_IMAGE}"

COPY . /

ENV GOOGLE_APPLICATION_CREDENTIALS="/modules/gac.json"

ENV DAGSTER_DISABLE_TELEMETRY=true

# This makes sure that logs show up immediately instead of being buffered
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

# dagster-celery specified twice to deal with pip resolution in pip 20.3.3 when only
# extras are specified
RUN pip install \
    -e modules/dagster \
    -e modules/dagster-graphql \
    -e modules/dagster-celery \
    -e modules/dagster-celery[flower,redis,kubernetes] \
    -e modules/dagster-webserver \
    -e modules/dagster-postgres \
    -e modules/dagster-pandas \
    -e modules/dagster-aws \
    -e modules/dagster-gcp \
    -e modules/dagster-k8s \
    -e modules/dagster-celery-k8s \
    -e modules/dagster-celery-docker \
    -e modules/dagster-docker \
    -e modules/dagster-airflow \
    -e modules/dagstermill \
    -e modules/dagster-pipes \
    -e . \
    pyparsing\<3.0.0 \
    # START
    # SUPPOSEDLY ONE OF THESE IS THE GOOD PIN???
    Mako==1.2.4 \
    markdown-it-py==3.0.0 \
    MarkupSafe==2.1.2 \
    matplotlib-inline==0.1.6 \
    mdurl==0.1.2 \
    mistune==3.0.2 \
    multidict==6.0.4 \
    nbclient==0.9.0 \
    nbconvert==7.16.0 \
    nbformat==5.9.2 \
    nest-asyncio==1.6.0 \
    numpy==1.24.2 \
    oauth2client==4.1.3 \
    oauthlib==3.2.2 \
    packaging==23.0 \
    pandas==1.5.3 \
    pandocfilters==1.5.1 \
    papermill==2.5.0 \
    parso==0.8.3 \
    pendulum==2.1.2 \
    pexpect==4.9.0 \
    pickleshare==0.7.5 \
    pkgutil_resolve_name==1.3.10 \
    # SUPPOSEDLY THESE ARE USELESS?
    # platformdirs==4.2.0 \
    # prometheus-client==0.16.0 \
    # prompt-toolkit==3.0.38 \
    # proto-plus==1.22.2 \
    # protobuf==4.22.1 \
    # psutil==5.9.8 \
    # psycopg2-binary==2.9.5 \
    # ptyprocess==0.7.0 \
    # pure-eval==0.2.2 \
    # py4j==0.10.9.7 \
    # pyarrow==11.0.0 \
    # pyasn1==0.4.8 \
    # pyasn1-modules==0.2.8 \
    # pydantic==1.10.6 \
    # Pygments==2.17.2 \
    # pyparsing==2.4.7 \
    # pyspark==3.5.0 \
    # python-dateutil==2.8.2 \
    # python-dotenv==1.0.0 \
    # pytz==2022.7.1 \
    # pytzdata==2020.1 \
    # PyYAML==6.0 \
    # pyzmq==25.1.2 \
    # END
    zipp==3.15.0

RUN ! (pip list --exclude-editable | grep -e dagster)

WORKDIR /dagster_test/test_project/

EXPOSE 80
