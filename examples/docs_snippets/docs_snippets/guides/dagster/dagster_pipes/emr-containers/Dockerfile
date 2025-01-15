FROM 895885662937.dkr.ecr.us-west-2.amazonaws.com/spark/emr-7.5.0:latest

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

USER root
RUN mkdir /python && chown hadoop:hadoop /python

USER hadoop
ENV UV_PYTHON_INSTALL_DIR=/python

RUN uv python install --python-preference only-managed 3.9.16
ENV PATH="${UV_PYTHON_INSTALL_DIR}/cpython-3.9.16-linux-x86_64-gnu/bin:${PATH}"
ENV UV_PYTHON="${UV_PYTHON_INSTALL_DIR}/cpython-3.9.16-linux-x86_64-gnu/bin/python" \
    UV_BREAK_SYSTEM_PACKAGES=1 \
    PYSPARK_PYTHON="${UV_PYTHON_INSTALL_DIR}/cpython-3.9.16-linux-x86_64-gnu/bin/python" \
    PYSPARK_DRIVER_PYTHON="${UV_PYTHON_INSTALL_DIR}/cpython-3.9.16-linux-x86_64-gnu/bin/python" \
    PYTHONPATH="${UV_PYTHON_INSTALL_DIR}/cpython-3.9.16-linux-x86_64-gnu/lib/python3.9/site-packages"

RUN uv pip install --system dagster-pipes boto3 pyspark

WORKDIR /app
COPY script.py .
