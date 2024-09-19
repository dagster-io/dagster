# home_dir = `pwd`
# echo `pwd`
HOME_DIR=$(pwd)
DAGSTER_DEPLOYMENT=prod DAGSTER_HOME=$HOME_DIR/prod_dagster_home/ dagster-webserver -f hn_dagster.py
