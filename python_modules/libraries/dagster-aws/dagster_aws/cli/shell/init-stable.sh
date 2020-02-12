#!/bin/bash

INSTALL_PATH="/opt/dagster"

# For updating nodejs
curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -

# For updating yarn
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list

# Install base deps
apt-get update && \
apt-get install -y \
    git make python3 python3-pip python-virtualenv nodejs yarn postgresql

# Create and chown install path
mkdir -p $INSTALL_PATH
chown -R ubuntu:ubuntu $INSTALL_PATH

# Set up a virtualenv for us to use
sudo -u ubuntu virtualenv --python=/usr/bin/python3 $INSTALL_PATH/venv

sudo -u ubuntu /bin/bash -c 'source /opt/dagster/venv/bin/activate && \
    pip install -U pip && \
    pip install dagster dagit dagster-aws'

# user code will go here
mkdir -p $INSTALL_PATH/app
chown -R ubuntu:ubuntu $INSTALL_PATH/app

# Setup default $DAGSTER_HOME
mkdir -p $INSTALL_PATH/dagster_home
chown -R ubuntu:ubuntu $INSTALL_PATH/dagster_home
echo 'export DAGSTER_HOME=$INSTALL_PATH/dagster_home' > ~/dagster_home.sh
chmod +x ~/dagster_home.sh
sudo mv ~/dagster_home.sh /etc/profile.d/dagster_home.sh

# Install systemd service
cat <<EOT > /lib/systemd/system/dagit.service
[Unit]
Description=Run Dagit
After=network.target

[Service]
Type=simple
User=ubuntu
ExecStart=/bin/bash -c 'export DAGSTER_HOME=/opt/dagster/dagster_home && export PYTHONPATH=$PYTHONPATH:/opt/dagster/app && export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && source /opt/dagster/venv/bin/activate && /opt/dagster/venv/bin/dagit -h 0.0.0.0 -p 3000 -y /opt/dagster/app/repository.yaml'
Restart=always
WorkingDirectory=/opt/dagster/app/

[Install]
WantedBy=multi-user.target
EOT

systemctl daemon-reload
systemctl enable dagit
