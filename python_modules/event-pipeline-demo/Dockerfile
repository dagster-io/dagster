FROM python:3.7.2-stretch

# We need to use java 8 because https://stackoverflow.com/questions/53583199/pyspark-error-unsupported-class-file-major-version-55
##################################################################################################
# https://github.com/docker-library/openjdk/blob/c3023e4da10d10e9c9775eabe2d7baac146e7ae1/8/jdk/slim/Dockerfile

# A few reasons for installing distribution-provided OpenJDK:
#
#  1. Oracle.  Licensing prevents us from redistributing the official JDK.
#
#  2. Compiling OpenJDK also requires the JDK to be installed, and it gets
#     really hairy.
#
#     For some sample build times, see Debian's buildd logs:
#       https://buildd.debian.org/status/logs.php?pkg=openjdk-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    bzip2 \
    unzip \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Default to UTF-8 file.encoding
ENV LANG C.UTF-8

# add a simple script that can auto-detect the appropriate JAVA_HOME value
# based on whether the JDK or only the JRE is installed
RUN { \
    echo '#!/bin/sh'; \
    echo 'set -e'; \
    echo; \
    echo 'dirname "$(dirname "$(readlink -f "$(which javac || which java)")")"'; \
    } > /usr/local/bin/docker-java-home \
    && chmod +x /usr/local/bin/docker-java-home

# do some fancy footwork to create a JAVA_HOME that's cross-architecture-safe
RUN ln -svT "/usr/lib/jvm/java-8-openjdk-$(dpkg --print-architecture)" /docker-java-home
ENV JAVA_HOME /docker-java-home

# Updated from base image
ENV JAVA_VERSION 8u212
ENV JAVA_DEBIAN_VERSION 8u212-b01-1~deb9u1 

RUN set -ex; \
    \
    # deal with slim variants not having man page directories (which causes "update-alternatives" to fail)
    if [ ! -d /usr/share/man/man1 ]; then \
    mkdir -p /usr/share/man/man1; \
    fi; \
    \
    apt-get update; \
    apt-get install -y --no-install-recommends \
    openjdk-8-jdk-headless="$JAVA_DEBIAN_VERSION" \
    ; \
    rm -rf /var/lib/apt/lists/*; \
    \
    # verify that "docker-java-home" returns what we expect
    [ "$(readlink -f "$JAVA_HOME")" = "$(docker-java-home)" ]; \
    \
    # update-alternatives so that future installs of other OpenJDK versions don't change /usr/bin/java
    update-alternatives --get-selections | awk -v home="$(readlink -f "$JAVA_HOME")" 'index($3, home) == 1 { $2 = "manual"; print | "update-alternatives --set-selections" }'; \
    # ... and verify that it actually worked for one of the alternatives we care about
    update-alternatives --query java | grep -q 'Status: manual'

##################################################################################################

# From https://github.com/gettyimages/docker-spark/blob/master/Dockerfile
# HADOOP
ENV HADOOP_VERSION 3.0.0
ENV HADOOP_HOME /usr/hadoop-$HADOOP_VERSION
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV PATH $PATH:$HADOOP_HOME/bin
RUN curl -sL --retry 3 \
    "http://archive.apache.org/dist/hadoop/common/hadoop-$HADOOP_VERSION/hadoop-$HADOOP_VERSION.tar.gz" \
    | gunzip \
    | tar -x -C /usr/ \
    && rm -rf $HADOOP_HOME/share/doc \
    && chown -R root:root $HADOOP_HOME

# SPARK
ENV SPARK_VERSION 2.4.0
ENV SPARK_PACKAGE spark-${SPARK_VERSION}-bin-without-hadoop
ENV SPARK_HOME /usr/spark-${SPARK_VERSION}
ENV SPARK_DIST_CLASSPATH="$HADOOP_HOME/etc/hadoop/*:$HADOOP_HOME/share/hadoop/common/lib/*:$HADOOP_HOME/share/hadoop/common/*:$HADOOP_HOME/share/hadoop/hdfs/*:$HADOOP_HOME/share/hadoop/hdfs/lib/*:$HADOOP_HOME/share/hadoop/hdfs/*:$HADOOP_HOME/share/hadoop/yarn/lib/*:$HADOOP_HOME/share/hadoop/yarn/*:$HADOOP_HOME/share/hadoop/mapreduce/lib/*:$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/share/hadoop/tools/lib/*"
ENV PATH $PATH:${SPARK_HOME}/bin
RUN curl -sL --retry 3 \
    "https://www.apache.org/dyn/mirrors/mirrors.cgi?action=download&filename=spark/spark-${SPARK_VERSION}/${SPARK_PACKAGE}.tgz" \
    | gunzip \
    | tar x -C /usr/ \
    && mv /usr/$SPARK_PACKAGE $SPARK_HOME \
    && chown -R root:root $SPARK_HOME



RUN mkdir -p /tmp/results

WORKDIR /

ADD dagster/requirements.txt dagster_requirements.txt
RUN pip install -r dagster_requirements.txt

ADD dagit/requirements.txt dagit_requirements.txt
RUN pip install -r dagit_requirements.txt

ADD event-pipeline-demo/requirements.txt .

RUN pip install -r requirements.txt

ADD dagster dagster
ADD dagit dagit

RUN pip install -e dagster/
RUN pip install -e dagit/

# Add this project
ADD event-pipeline-demo .

# Install Python requirements for your repository
RUN pip install -r requirements.txt

RUN mkdir -p /data/raw/2019/01/01/
RUN curl -sL --retry 3 \
    "https://s3.us-east-2.amazonaws.com/elementl-public/example-json.gz" \
    | gunzip > /data/raw/2019/01/01/data \
    && chown -R root:root /data

# The dagster-airflow machinery will use Dagit's GraphQL server to execute steps in your
# pipelines, so we need to run Dagit (by default on port 3000) when the container starts up
ENTRYPOINT [ "dagit", "--no-watch" ]
EXPOSE 3000