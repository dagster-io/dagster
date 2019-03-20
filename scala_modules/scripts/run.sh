#!/bin/bash

sbt events/assembly

JARFILE=`pwd`/events/target/scala-2.11/events-assembly-0.1.0-SNAPSHOT.jar

# Run it locally
${SPARK_HOME}/bin/spark-submit \
    --class "io.dagster.events.EventPipeline" \
    --master "local[4]" \
    $JARFILE \
    "$@"


