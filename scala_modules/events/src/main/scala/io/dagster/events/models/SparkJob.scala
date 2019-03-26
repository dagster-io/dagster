package io.dagster.events.models

import org.apache.log4j.{Level, LogManager}
import org.apache.spark.SparkContext
import org.apache.spark.sql.SparkSession

abstract class SparkJob {
  final lazy val spark: SparkSession = SparkSession.builder.getOrCreate()
  final lazy val sc: SparkContext = spark.sparkContext
  final lazy val log = LogManager.getLogger(this.getClass.getName)

  def run(args: Array[String]): Unit

  def main(args: Array[String]): Unit = {
    log.setLevel(Level.INFO)

    run(args: Array[String])
  }
}
