/** This package provides a simple hello world example for reading JSON events from the filesystem, S3, or GCS, and
  * writing them out as Parquet.
  *
  * ==Overview==
  * To build this jar, run:
  *
  *    make all
  *
  * in the scala_modules root. To run, you'll need to invoke via spark-submit with appropriate CLI args, for example:
  *
  *    spark-submit \
  *        --class io.dagster.events.EventPipeline \
  *        --master "local[*]" \
  *        --driver-memory 24g \
  *        --deploy-mode client \
  *        events/target/scala-2.11/events-assembly-0.1.0-SNAPSHOT.jar \
  *        --gcs-input-bucket input_bucket \
  *        --gcs-output-bucket output_bucket \
  *        --date 2019-05-28
  *
  */
package io.dagster.events

import org.apache.spark.sql.Dataset
import java.util.Date

import com.amazonaws.services.s3.AmazonS3ClientBuilder

import scala.reflect.internal.FatalError
import scala.io.Source
import models._

object EventPipeline extends SparkJob {
  final val numSampleEvents = 20

  import spark.implicits._

  def readEvents(backend: StorageBackend, date: Date): Dataset[Event] = {
    // Read event records from local path, GCS, or S3
    val records = backend match {
      case l: LocalStorageBackend => spark.read.textFile(l.inputPath)
      case g: GCSStorageBackend   => spark.read.textFile(g.inputPath)
      case s: S3StorageBackend =>
        s.getS3Objects(date)
          .toDS()
          .mapPartitions { part =>
            // S3 client objects are not serializable, so we need to instantiate each on the executors, not on the master.
            val client = AmazonS3ClientBuilder.defaultClient
            part.flatMap { key =>
              Source
                .fromInputStream(client.getObject(s.bucket, key).getObjectContent)
                .getLines

            }
          }
    }
    records.flatMap(Event.fromString)
  }

  override def run(args: Array[String]) {
    val conf = EventPipelineConfig.parse(args)

    // Create an ADT StorageBackend to abstract away which we're talking to
    val backend: StorageBackend =
      (conf.localPath, conf.s3Bucket, conf.s3Prefix, conf.gcsInputBucket, conf.gcsOutputBucket) match {
        case (_, Some(bucket), Some(prefix), _, _)            => S3StorageBackend(bucket, prefix, conf.date)
        case (Some(path), _, _, _, _)                         => LocalStorageBackend(path, conf.date)
        case (_, _, _, Some(inputBucket), Some(outputBucket)) => GCSStorageBackend(inputBucket, outputBucket, conf.date)
        case _                                                => throw new IllegalArgumentException("Error, invalid arguments")
      }

    val events = readEvents(backend, conf.date)

    // Print a few records in debug logging
    events
      .take(numSampleEvents)
      .foreach(log.debug)

    // Ensure output path is empty
    backend.ensureOutputEmpty()

    // Write event records as Parquet
    events
      .toDF()
      .write
      .parquet(backend.outputURI)
  }
}

case class EventPipelineConfig(
  s3Bucket: Option[String] = None,
  s3Prefix: Option[String] = None,
  gcsInputBucket: Option[String] = None,
  gcsOutputBucket: Option[String] = None,
  localPath: Option[String] = None,
  date: Date = new Date()
)

object EventPipelineConfig {
  val dateFormat = new java.text.SimpleDateFormat("yyyy-MM-dd")

  val parser: scopt.OptionParser[EventPipelineConfig] = new scopt.OptionParser[EventPipelineConfig]("EventPipeline") {
    opt[String]("s3-bucket")
      .action((x, c) => c.copy(s3Bucket = Some(x)))
      .text("S3 bucket to read")
      .validate(x => if (x.startsWith("s3://")) { failure("bucket should not include s3:// prefix") } else { success })

    opt[String]("s3-prefix")
      .action((x, c) => c.copy(s3Prefix = Some(x)))
      .text("S3 prefix to read")

    opt[String]("gcs-input-bucket")
      .action((x, c) => c.copy(gcsInputBucket = Some(x)))
      .text("GCS input bucket to read")
      .validate(
        x => if (x.startsWith("gs://")) { failure("gcs-input-bucket should not include gs:// prefix") } else { success }
      )

    opt[String]("gcs-output-bucket")
      .action((x, c) => c.copy(gcsOutputBucket = Some(x)))
      .text("GCS output bucket to write")
      .validate(
        x =>
          if (x.startsWith("gs://")) { failure("gcs-output-bucket should not include gs:// prefix") } else { success }
      )

    opt[String]("local-path")
      .action((x, c) => c.copy(localPath = Some(x)))
      .text("Local path prefix")

    opt[String]("date")
      .required()
      .action((x, c) => c.copy(date = dateFormat.parse(x)))

    checkConfig { c =>
      // Must be configured for one of local, S3, or GCS only
      val numDefined = Seq(
        c.localPath.isDefined,
        c.s3Bucket.isDefined | c.s3Prefix.isDefined,
        c.gcsInputBucket.isDefined | c.gcsOutputBucket.isDefined
      ).map { x =>
        if (x) 1 else 0
      }.sum

      if (numDefined == 1) {
        if (c.s3Bucket.isDefined & c.s3Prefix.isEmpty) {
          failure("Both S3 bucket and prefix must be defined")
        } else if (c.gcsInputBucket.isDefined & c.gcsOutputBucket.isEmpty) {
          failure("Both GCS input and output bucket must be defined")
        } else {
          success
        }
      } else {
        failure("Only one of (local-path), (S3 bucket/prefix), (GCS input/output buckets) may be defined")
      }
    }
  }

  def parse(args: Array[String]): EventPipelineConfig =
    parser.parse(args, EventPipelineConfig()).getOrElse {
      throw FatalError("Incorrect options")
    }
}
