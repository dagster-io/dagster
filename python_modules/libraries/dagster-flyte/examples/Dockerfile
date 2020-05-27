ARG PYTHON_VERSION

FROM python:"${PYTHON_VERSION}"

WORKDIR /app
ENV VENV /app/venv
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONPATH /app

# Set up a virtual environment to use with our workflows
RUN python -m venv ${VENV}
RUN ${VENV}/bin/pip install wheel

COPY ./requirements.txt .
RUN ${VENV}/bin/pip install -r requirements.txt
RUN ${VENV}/bin/pip install awscli

# This is a script that enables a virtualenv, copy it to a better location
RUN cp ${VENV}/bin/flytekit_venv /opt/

# Copy the rest of the code
COPY . .

# Set this environment variable. It will be used by the flytekit SDK during the registration/compilation steps
ARG IMAGE_TAG
ENV FLYTE_INTERNAL_IMAGE "$IMAGE_TAG"

# Enable the virtualenv for this image. Note this relies on the VENV variable we've set in this image.
ENTRYPOINT ["/opt/flytekit_venv"]