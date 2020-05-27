FROM gitpod/workspace-full

USER gitpod

# Install wxPython dependencies
RUN sudo apt-get -q update

ENV DAGSTER_HOME="$HOME/dagster_home"
RUN mkdir -p $DAGSTER_HOME