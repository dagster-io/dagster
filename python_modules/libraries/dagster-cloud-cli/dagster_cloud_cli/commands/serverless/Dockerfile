# base image is templated in (default: python:3.11-slim)

# copy both requirements.txt / setup.py to guarantee that at least one file will be copied over
# for any pre-src COPY.  On some flavors of Docker (Linux), the COPY command will fail unless there
# exists at least one file to copy over.
COPY *dagster_cloud_pre_install.sh *setup.py *requirements.txt /
RUN if [ -f "dagster_cloud_pre_install.sh" ]; then \
        ./dagster_cloud_pre_install.sh; \
    fi

# This is to enable Docker caching - if setup.py exists, we install the dependencies before
# copying all other files
RUN if [ -f "setup.py" ]; then \
        pip install .; \
    fi

WORKDIR /opt/dagster/app
COPY . /opt/dagster/app

# Install the rest of dependencies in case there is a requirements.txt
# Note: this happens after the src COPY command into the working directory, to ensure that any
# editable installs will still work
RUN if [ -f "requirements.txt" ]; then \
        pip install -r requirements.txt; \
    fi

# Run the custom dagster cloud post install script if available
RUN if [ -f "dagster_cloud_post_install.sh" ]; then \
        ./dagster_cloud_post_install.sh; \
    fi

# Make sure dagster-cloud is installed. Fail early here if not.
RUN if ! dagster-cloud --version; then \
        echo "Could not find the dagster-cloud package.  Make sure you include the dagster-cloud package in your setup.py or requirements.txt file to ensure that it is installed as part of your workspace."; \
        exit 1; \
    fi
