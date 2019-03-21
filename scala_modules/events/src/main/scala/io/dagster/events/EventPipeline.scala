package io.dagster.events

import java.io.InputStream

import org.apache.spark.sql.SparkSession
import java.util.Date

import com.amazonaws.services.s3._
import model._

import scala.reflect.internal.FatalError
import scala.collection.JavaConversions._
import scala.io.Source

import models.Event


object EventPipeline {
  val s3Client = AmazonS3ClientBuilder.defaultClient()

  def getS3Objects(bucket: String, prefix: String, date: Date): Seq[String] = {
    // We first retrieve a list of S3 filenames under our bucket prefix, then process.
    // See: https://tech.kinja.com/how-not-to-pull-from-s3-using-apache-spark-1704509219

    val formattedDate = new java.text.SimpleDateFormat("yyyy/MM/dd").format(date)

    val s3prefix = s"$prefix/$formattedDate/"
    val request = new ListObjectsRequest()
    request.setBucketName(bucket)
    request.setPrefix(s3prefix)

    s3Client
      .listObjects(request)
      .getObjectSummaries
      .toList
      .map(_.getKey)
  }

  def main(args: Array[String]) {
    val spark = SparkSession.builder.appName("EventPipeline").getOrCreate()

    val conf = EventPipelineConfig.parse(args)

    val objectKeys = getS3Objects(conf.s3Bucket, conf.s3Prefix, conf.date)

    val records = spark.sparkContext.parallelize(objectKeys)
      .flatMap {
        key =>
          Source.fromInputStream(s3Client.getObject(conf.s3Bucket, key).getObjectContent: InputStream).getLines
      }
      .flatMap(Event.fromString)

    records
      .take(100)
      .foreach(println)
  }
}

case class EventPipelineConfig(
  s3Bucket: String = "",
  s3Prefix: String = "",
  date: Date = new Date()
)

object EventPipelineConfig {
  val dateFormat = new java.text.SimpleDateFormat("yyyy-MM-dd")

  val parser = new scopt.OptionParser[EventPipelineConfig]("EventPipeline") {
    opt[String]("s3-bucket")
      .required()
      .action((x, c) => c.copy(s3Bucket = x))
      .text("S3 bucket to read")

    opt[String]("s3-prefix")
      .required()
      .action((x, c) => c.copy(s3Prefix = x))
      .text("S3 prefix to read")

    opt[String]("date")
      .required()
      .action((x, c) => c.copy(date = dateFormat.parse(x)))
  }

  def parse(args: Array[String]): EventPipelineConfig = parser.parse(args, EventPipelineConfig()).getOrElse {
    throw new FatalError("Incorrect options")
  }
}