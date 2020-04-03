#!/bin/sh


# This block may be omitted if not packaging a repository with cron schedules
####################################################################################################
# see: https://unix.stackexchange.com/a/453053 - fixes inflated hard link count
touch /etc/crontab /etc/cron.*/*

service cron start

export DAGSTER_HOME=/opt/dagster/dagster_home

# Add all schedules
dagster schedule up

# Restart previously running schedules
dagster schedule restart --restart-all-running
####################################################################################################

DAGSTER_HOME=/opt/dagster/dagster_home dagit -h 0.0.0.0 -p 3000
