FROM python:3.8.3-slim

# Next two commands lifted from https://github.com/jpetazzo/dind/blob/master/Dockerfile

# Let's start with some basic stuff.
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    lxc \
    iptables

RUN curl -sSL https://get.docker.com/ > install_docker.sh

# Now we usage a multistage build to remove the cruft above
# that was needed to get the shell script

FROM python:3.8.3-slim

COPY --from=0 install_docker.sh .

RUN sh install_docker.sh

ADD requirements.txt .

RUN pip install -r requirements.txt