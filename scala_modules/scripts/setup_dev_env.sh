#!/usr/bin/env bash

set -eux


if [[ -z "${GOOGLE_APPLICATION_CREDENTIALS}" ]]; then
    echo "GOOGLE_APPLICATION_CREDENTIALS not set, please set then continue"
    exit 1
fi

if [[ -z "${AWS_ACCESS_KEY_ID}" ]]; then
    echo "AWS_ACCESS_KEY_ID not set, please set then continue"
    exit 1
fi

if [[ -z "${AWS_SECRET_ACCESS_KEY}" ]]; then
    echo "AWS_SECRET_ACCESS_KEY not set, please set then continue"
    exit 1
fi


SPARK_VERSION="2.4.3"
GCS_CONNECTOR_VERSION="hadoop2-1.9.17"
HADOOP_AWS_VERSION="2.7.1"

# assumes we're stashing Spark under ~/src_ext
BASE_PATH="${HOME}/src_ext"
SPARK_HOME="${BASE_PATH}/spark"

# Download Spark archive
wget "http://ftp.wayne.edu/apache/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop2.7.tgz" -O "${BASE_PATH}/spark-${SPARK_VERSION}.tgz"

# Extract Spark archive
tar xzf "${BASE_PATH}/spark-${SPARK_VERSION}.tgz" -C "${BASE_PATH}"

# Symlink ~/src_ext/spark to latest version e.g. ~/src_ext/spark-2.4.3-bin-hadoop2.7
ln -s "${BASE_PATH}/spark-${SPARK_VERSION}-bin-hadoop2.7" "${SPARK_HOME}"

# Write spark-defaults.conf
cat >> "${SPARK_HOME}/conf/spark-defaults.conf" <<EOL
spark.hadoop.google.cloud.auth.service.account.enable       true
spark.hadoop.google.cloud.auth.service.account.json.keyfile $GOOGLE_APPLICATION_CREDENTIALS
spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.access.key=$AWS_ACCESS_KEY_ID
spark.hadoop.fs.s3a.secret.key=$AWS_SECRET_ACCESS_KEY
EOL

# Download connector jars to $SPARK_HOME/jars
wget "http://repo2.maven.org/maven2/com/google/cloud/bigdataoss/gcs-connector/${GCS_CONNECTOR_VERSION}/gcs-connector-${GCS_CONNECTOR_VERSION}-shaded.jar" -O "${SPARK_HOME}/jars/gcs-connector-${GCS_CONNECTOR_VERSION}-shaded.jar"
wget "http://search.maven.org/remotecontent?filepath=org/apache/hadoop/hadoop-aws/${HADOOP_AWS_VERSION}/hadoop-aws-${HADOOP_AWS_VERSION}.jar" -O "${SPARK_HOME}/jars/hadoop-aws-${HADOOP_AWS_VERSION}.jar"
