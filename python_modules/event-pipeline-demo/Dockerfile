# You may use any base container with a supported Python runtime: 2.7, 3.5, 3.6, or 3.7
FROM python:3.7

# Install any OS-level requirements (e.g. using apt, yum, apk, etc.) that the pipelines in your
# repository require to run
# RUN apt-get install some-package some-other-package

# Set environment variables that you'd like to have available in the built image.
# ENV IMPORTANT_OPTION=yes

# If you would like to set secrets at build time (with --build-arg), set args
# ARG super_secret

# Install Dagit
RUN pip install dagit

# Add this project
ADD . .

# Install Python requirements for your repository
RUN pip install -r requirements.txt

# The dagster-airflow machinery will use Dagit's GraphQL server to execute steps in your
# pipelines, so we need to run Dagit (by default on port 3000) when the container starts up
ENTRYPOINT [ "dagit" ]
EXPOSE 3000