package io.dagster.events

import org.apache.spark.sql.SparkSession
import java.util.Date

object EventPipeline {
  def main(args: Array[String]) {
    val spark = SparkSession.builder.appName("EventPipeline").getOrCreate()

    EventPipelineConfig.parse(args).map {
      config => {

        println(config)
        val df = spark.read.json(s"s3n://${config.s3Bucket}/${config.s3Prefix}")
        df.printSchema()
      }
    }
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

  def parse(args: Array[String]): Option[EventPipelineConfig] = parser.parse(args, EventPipelineConfig())
}