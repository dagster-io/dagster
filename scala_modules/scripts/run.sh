#!/bin/bash
set -ex 

sbt events/assembly

JARFILE="./events/target/scala-2.11/events-assembly-0.1.0-SNAPSHOT.jar"

# Test for spark home set
if [ -z "SPARK_HOME" ]; then
    echo "Set SPARK_HOME to your spark installation to continue."
    exit 1
fi

# Run it locally
${SPARK_HOME}/bin/spark-submit \
    --class "io.dagster.events.EventPipeline" \
    --master "local[4]" \
    $JARFILE \
    "$@"


