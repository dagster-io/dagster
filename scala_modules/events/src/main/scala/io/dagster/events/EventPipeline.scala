package io.dagster.events
/** This package provides a simple hello world example for reading JSON events from S3 and writing those events back to
  * S3 as parquet.
  *
  * ==Overview==
  * Note that a script is provided to simplify running this; you can invoke with:
  *
  * ./scripts/run.sh --s3-bucket "YOUR BUCKET" --s3-prefix "YOUR PREFIX" --date "2019-01-01"
  *
  * Note that Spark is expected to be a provided dependency, and you should set $SPARK_HOME to point to the location
  * of your Spark installation.
  *
  * Also you will need the following jar on your classpath (preferably placed in $SPARK_HOME/jars):
  * http://search.maven.org/remotecontent?filepath=org/apache/hadoop/hadoop-aws/2.7.1/hadoop-aws-2.7.1.jar
  *
  * Finally, you should edit $SPARK_HOME/conf/spark-defaults.conf to contain the following:
  *
  * spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem
  * spark.hadoop.fs.s3a.access.key=YOUR_ACCESS_KEY
  * spark.hadoop.fs.s3a.secret.key=YOUR_SECRET_KEY
  *
  * ==References==
  * Spark + S3: http://deploymentzone.com/2015/12/20/s3a-on-spark-on-aws-ec2/
  * Spark reading from S3: https://tech.kinja.com/how-not-to-pull-from-s3-using-apache-spark-1704509219
  *
  * ==Notes==
  * Getting AWS S3 to play nice with Spark is complicated, because it involves a dependency on both aws-java-sdk and
  * hadoop-aws, and these two libraries need to be compatible versions (and compatible with Spark) or else everything
  * explodes:
  *
  * https://hadoop.apache.org/docs/current/hadoop-aws/tools/hadoop-aws/index.html#Missing_method_in_com.amazonaws_class
  *
  * We currently use AWS 1.7.4 and hadoop-aws 2.7.1 as these are known to be compatible and work with Spark 2.4.0.
  */

import java.io.InputStream

import org.apache.spark.sql.SparkSession
import java.util.Date

import com.amazonaws.auth.BasicAWSCredentials
import com.amazonaws.services.s3._
import model._

import scala.reflect.internal.FatalError
import scala.collection.JavaConversions._
import scala.io.Source
import models.Event


object EventPipeline {
  final lazy val spark = SparkSession.builder.appName("EventPipeline").getOrCreate()
  final lazy val s3Client = new AmazonS3Client(new BasicAWSCredentials(
    spark.sparkContext.getConf.get("spark.hadoop.fs.s3a.access.key"),
    spark.sparkContext.getConf.get("spark.hadoop.fs.s3a.secret.key")
  ))
  final lazy val datePathFormatter = new java.text.SimpleDateFormat("yyyy/MM/dd")


  def getS3Objects(bucket: String, prefix: String, date: Date): Seq[String] = {
    // We first retrieve a list of S3 filenames under our bucket prefix, then process.
    // See: https://tech.kinja.com/how-not-to-pull-from-s3-using-apache-spark-1704509219

    val formattedDate = datePathFormatter.format(date)
    val s3prefix = s"$prefix/raw/$formattedDate/"
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
    // Parse command line arguments
    val conf = EventPipelineConfig.parse(args)

    val objectKeys = getS3Objects(conf.s3Bucket, conf.s3Prefix, conf.date)

    // Read event records from S3 date partition
    val records = spark.sparkContext.parallelize(objectKeys)
      .flatMap {
        key =>
          Source.fromInputStream(s3Client.getObject(conf.s3Bucket, key).getObjectContent: InputStream).getLines
      }
      .flatMap(Event.fromString)

    // Print a few records
    records
      .take(100)
      .foreach(println)

    // Write event records to S3 as Parquet
    import spark.implicits._
    records
      .toDF()
      .write
      .parquet(s"s3a://${conf.s3Bucket}/${conf.s3Prefix}/output/${datePathFormatter.format(conf.date)}")
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