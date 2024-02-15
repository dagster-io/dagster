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
    alembic==1.10.2 \
    amqp==5.1.1 \
    aniso8601==9.0.1 \
    anyio==3.6.2 \
    asttokens==2.4.1 \
    async-timeout==4.0.2 \
    attrs==23.2.0 \
    backcall==0.2.0 \
    backoff==2.2.1 \
    beautifulsoup4==4.12.3 \
    billiard==3.6.4.0 \
    bleach==6.1.0 \
    boto3==1.26.89 \
    botocore==1.29.89 \
    cachetools==5.3.0 \
    celery==5.2.7 \
    certifi==2022.12.7 \
    charset-normalizer==3.1.0 \
    click==8.1.3 \
    click-didyoumean==0.3.0 \
    click-plugins==1.1.1 \
    click-repl==0.2.0 \
    coloredlogs==14.0 \
    comm==0.2.1 \
    croniter==1.3.8 \
    db-dtypes==1.0.5 \
    debugpy==1.8.1 \
    decorator==5.1.1 \
    defusedxml==0.7.1 \
    docker==5.0.3 \
    docker-image-py==0.1.12 \
    docstring-parser==0.15 \
    entrypoints==0.4 \
    executing==2.0.1 \
    fastjsonschema==2.19.1 \
    flower==1.2.0 \
    fsspec==2023.3.0 \
    google-api-core==2.11.0 \
    google-api-python-client==2.80.0 \
    google-auth==2.16.2 \
    google-auth-httplib2==0.1.0 \
    google-cloud-bigquery==3.6.0 \
    google-cloud-core==2.3.2 \
    google-cloud-storage==2.7.0 \
    google-crc32c==1.5.0 \
    google-resumable-media==2.4.1 \
    googleapis-common-protos==1.58.0 \
    gql==3.4.0 \
    graphene==3.2.1 \
    graphql-core==3.2.3 \
    graphql-relay==3.2.0 \
    greenlet==2.0.2 \
    grpcio==1.47.5 \
    grpcio-health-checking==1.47.5 \
    grpcio-status==1.47.5 \
    h11==0.14.0 \
    httplib2==0.21.0 \
    httptools==0.5.0 \
    humanfriendly==10.0 \
    humanize==4.6.0 \
    idna==3.4 \
    importlib-metadata==6.0.0 \
    importlib-resources==5.12.0 \
    ipykernel==6.29.2 \
    ipython==8.12.3 \
    ipython-genutils==0.2.0 \
    jedi==0.19.1 \
    Jinja2==3.1.2 \
    jmespath==1.0.1 \
    jsonschema==4.21.1 \
    jsonschema-specifications==2023.12.1 \
    jupyter_client==7.4.9 \
    jupyter_core==5.7.1 \
    jupyterlab_pygments==0.3.0 \
    kombu==5.2.4 \
    kubernetes==26.1.0 \
    lazy-object-proxy==1.10.0 \
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
    platformdirs==4.2.0 \
    prometheus-client==0.16.0 \
    prompt-toolkit==3.0.38 \
    proto-plus==1.22.2 \
    protobuf==4.22.1 \
    psutil==5.9.8 \
    psycopg2-binary==2.9.5 \
    ptyprocess==0.7.0 \
    pure-eval==0.2.2 \
    py4j==0.10.9.7 \
    pyarrow==11.0.0 \
    pyasn1==0.4.8 \
    pyasn1-modules==0.2.8 \
    pydantic==1.10.6 \
    Pygments==2.17.2 \
    pyparsing==2.4.7 \
    pyspark==3.5.0 \
    python-dateutil==2.8.2 \
    python-dotenv==1.0.0 \
    pytz==2022.7.1 \
    pytzdata==2020.1 \
    PyYAML==6.0 \
    pyzmq==25.1.2 \
    redis==4.5.1 \
    referencing==0.33.0 \
    regex==2023.12.25 \
    requests==2.28.2 \
    requests-oauthlib==1.3.1 \
    requests-toolbelt==0.10.1 \
    rich==13.7.0 \
    rpds-py==0.18.0 \
    rsa==4.9 \
    s3transfer==0.6.0 \
    scrapbook==0.5.0 \
    six==1.16.0 \
    sniffio==1.3.0 \
    soupsieve==2.5 \
    SQLAlchemy==1.4.46 \
    stack-data==0.6.3 \
    starlette==0.26.0.post1 \
    structlog==24.1.0 \
    tabulate==0.9.0 \
    tenacity==8.2.3 \
    tinycss2==1.2.1 \
    tomli==2.0.1 \
    toposort==1.10 \
    tornado==6.2 \
    tqdm==4.65.0 \
    traitlets==5.14.1 \
    typing_extensions==4.5.0 \
    universal_pathlib==0.0.22 \
    uritemplate==4.1.1 \
    urllib3==1.26.15 \
    uvicorn==0.21.0 \
    uvloop==0.17.0 \
    vine==5.0.0 \
    watchdog==2.3.1 \
    watchfiles==0.18.1 \
    wcwidth==0.2.6 \
    webencodings==0.5.1 \
    websocket-client==1.5.1 \
    websockets==10.4 \
    yarl==1.8.2 \
    zipp==3.15.0

RUN ! (pip list --exclude-editable | grep -e dagster)

WORKDIR /dagster_test/test_project/

EXPOSE 80
