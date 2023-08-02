HOME_DIR=$(pwd)
DAGSTER_DEPLOYMENT=my-featured-branch DAGSTER_HOME=$HOME_DIR/dev_dagster_home/ dagster-webserver -f hn_dagster.py -p 3001
