package io.dagster.events.models

import com.amazonaws.auth.BasicAWSCredentials
import com.amazonaws.services.s3.AmazonS3Client
import org.apache.log4j.{Level, LogManager}
import org.apache.spark.sql.SparkSession


trait SparkJob {
  final lazy val spark = SparkSession.builder.getOrCreate()
  final lazy val log = LogManager.getLogger(this.getClass.getName)
  final lazy val s3Client = new AmazonS3Client(new BasicAWSCredentials(
    spark.sparkContext.getConf.get("spark.hadoop.fs.s3a.access.key"),
    spark.sparkContext.getConf.get("spark.hadoop.fs.s3a.secret.key")
  ))


  def run(args: Array[String]): Unit

  def main(args: Array[String]): Unit = {
    log.setLevel(Level.INFO)

    run(args: Array[String])
  }
}
