# You may use any base container with a supported Python runtime: 2.7, 3.5, 3.6, or 3.7
FROM python:3.7

# Install any OS-level requirements (e.g. using apt, yum, apk, etc.) that the pipelines in your
# repository require to run
# RUN apt-get install some-package some-other-package

# Set environment variables that you'd like to have available in the built image.
# ENV IMPORTANT_OPTION=yes

# If you would like to set secrets at build time (with --build-arg), set args
# ARG super_secret

# Install any Python requirements that the pipelines in your repository require to run
ADD /path/to/requirements.txt .
RUN pip install -r requirements.txt

# Add the Python file in which your repository is defined, and any local dependencies (e.g.,
# unpackaged Python files from which your repository definition imports, or local packages that
# cannot be installed using the requirements.txt).
ADD /path/to/workspace.yaml .
ADD /path/to/repository_definition.py .
# ADD /path/to/additional_file.py .
