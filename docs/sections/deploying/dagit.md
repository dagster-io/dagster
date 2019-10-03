# Standalone Dagit

The simplest way to deploy Dagster / Dagit is in standalone mode. You can deploy Dagit as a service
in your environment; several options for configuring this are described below.

## AWS Quick Start

**_NOTE: This is not intended to be a secure configuration, and the instance launched here will be
publicly accessible. For production settings, you should consider the manual configuration described
below._**

If you are on AWS, there is a quick start CLI utility in `dagster-aws` to automate the setup
process. Ensure you have AWS credentials on your local machine, and run:

```bash
pip install dagster dagit dagster-aws
dagster-aws init
```

This script will walk you through setting up an EC2 VM instance to host Dagit, as well as creating a
security group and key pair along the way. Once completed, the configuration for this is stored on
your local machine in `$DAGSTER_HOME/.dagit-aws-config`; subsequent usage of `dagster-aws` will use
this configuration to connect to your running EC2 instance.

This script will optionally launch an RDS instance for you; if you choose to launch an RDS
PostgreSQL instance, the remote EC2 instance will automatically be configured to talk to RDS via a
`dagster.yaml` file in the remote `$DAGSTER_HOME`. See the docs on
[`DagsterInstance`](https://dagster.readthedocs.io/en/latest/sections/deploying/instance.html) for
more information about this configuration.

Once the EC2 instance is launched and ready, you can synchronize your Dagster code to it using:

```bash
cd /path/to/your/dagster/code
dagster-aws up
```

This will copy over your Dagster client code to the EC2 instance and launch Dagit as `systemd`
service, and finally open a browser to Dagit. You can look at
[init.sh](https://github.com/dagster-io/dagster/blob/master/python_modules/libraries/dagster-aws/dagster_aws/cli/shell/init.sh)
for details on how we initialize the VM for running Dagit and the specification of the `systemd`
service.

The `dagster-aws` CLI saves its state to `$DAGSTER_HOME/dagster-aws-config.yaml`, so you can inspect
that file to understand what's going on and/or debug any issues.

## Manually Configuring Dagit

The `dagster-aws` CLI above is an easy way to get started, but makes a variety of simplifying
assumptions about your environment. In reality you may need to host Dagit in a particular VPC,
behind a reverse proxy, etc.

There are a couple of ways you can run Dagit internally, which we cover below.

### Run on a VM

To launch Dagit on a bare VM, ensure that you've got a recent Python version (preferably 3.7, but
2.7, 3.5, 3.6, and 3.7 are supported), and preferably a virtualenv configured. Then, you can install
Dagster and any libraries you need:

```bash
virtualenv --python=/usr/bin/python3 /some/path/to/venv
source /some/path/to/venv/bin/activate
pip install dagster dagit dagster-aws # ... any other dagster libraries you need, e.g. dagster-bash
```

To run Dagit, you can run something like the following:

```bash
export DAGSTER_HOME=/some/path/to/dagster_home
dagit --no-watch -h 0.0.0.0 -p 3000
```

In this configuration, Dagit will write execution logs to `$DAGSTER_HOME/logs` and listen on port

3000. To run Dagit as a long-lived service on this host, you can install a systemd service similar
      to the AWS quick start, with something like:

```
[Unit]
Description=Run Dagit
After=network.target

[Service]
Type=simple
User=ubuntu
ExecStart=/bin/bash -c '\
    export DAGSTER_HOME=/opt/dagster/dagster_home && \
    export PYTHONPATH=$PYTHONPATH:/opt/dagster/app && \
    export LC_ALL=C.UTF-8 && \
    export LANG=C.UTF-8 && \
    source /opt/dagster/venv/bin/activate && \
    /opt/dagster/venv/bin/dagit \
        --no-watch \
        -h 0.0.0.0 \
        -p 3000 \
        -y /opt/dagster/app/repository.yaml
Restart=always
WorkingDirectory=/opt/dagster/app/

[Install]
WantedBy=multi-user.target
```

Note that this assumes you've got a virtualenv for Dagster at `/opt/dagster/venv` and your client
code and `repository.yaml` are located at `/opt/dagster/app`.

## Containerized Execution in Docker

If you are running on AWS ECS, Kubernetes, or some other container-based orchestration, you'll
likely want to containerize Dagit using Docker.

A minimal skeleton Dockerfile that will run Dagit is shown below:

```Dockerfile
FROM dagster:dagster/py3.7.4

RUN set -ex \
    && pip install -U pip setuptools wheel \
    && pip install dagster dagit

WORKDIR /

# Here, we assume your Dagster client code is in the current directory
# including a repository.yaml file.
ADD . /

EXPOSE 3000

ENTRYPOINT [ "dagit", "--no-watch", "-h", "0.0.0.0", "-p", "3000" ]
```

This is based on the [public Docker
images](https://cloud.docker.com/u/dagster/repository/docker/dagster/dagster). We publish versions
for Python 2.7, 3.5, 3.6, and 3.7.
