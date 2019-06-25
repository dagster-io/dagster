#!/bin/bash

set -eux

rabbitmqctl stop_app
rabbitmqctl reset
rabbitmqctl start_app
