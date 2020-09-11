package io.dagster.events.models

import java.io.File
import java.util.Date

import com.amazonaws.services.s3.AmazonS3ClientBuilder
import com.amazonaws.services.s3.model.{DeleteObjectRequest, ListObjectsRequest, S3ObjectSummary}
import com.google.cloud.storage.StorageOptions
import com.google.cloud.storage.Storage.BlobListOption
import io.dagster.events.EventPipeline.log

import scala.collection.JavaConversions._
import scala.reflect.io.Directory

sealed trait StorageBackend {
  final val inputPrefix = "raw"
  final val outputPrefix = "output"
  final val dateFormatter = new java.text.SimpleDateFormat("yyyy/MM/dd")

  def outputURI: String
  def ensureOutputEmpty(): Unit
}

final case class LocalStorageBackend(path: String, date: Date) extends StorageBackend {
  val inputPath: String = s"$path/$inputPrefix/${dateFormatter.format(date)}"
  val outputPath: String = s"$path/$outputPrefix/${dateFormatter.format(date)}"

  override def outputURI: String = outputPath

  override def ensureOutputEmpty(): Unit = {
    val file = new File(outputURI)
    if (file.exists && file.isDirectory) {
      log.info(s"Removing local output files at $outputURI")
      Directory(file).deleteRecursively()
    }
  }
}

final case class S3StorageBackend(bucket: String, prefix: String, date: Date) extends StorageBackend {
  val inputPath: String = s"$prefix/$inputPrefix/${dateFormatter.format(date)}"
  val outputPath: String = s"$prefix/$outputPrefix/${dateFormatter.format(date)}"

  override def outputURI: String = s"s3a://$bucket/$outputPath"

  override def ensureOutputEmpty(): Unit = {
    val s3Client = AmazonS3ClientBuilder.defaultClient
    val objs = s3Client.listObjects(bucket, outputPath).getObjectSummaries

    if (!objs.isEmpty) {
      log.info(s"Removing contents of S3 output at path $outputURI")

      objs.foreach { obj: S3ObjectSummary =>
        log.info(s"Deleting S3 object ${obj.getKey}")
        val request = new DeleteObjectRequest(bucket, obj.getKey)
        s3Client.deleteObject(request)
      }
    }
  }

  def getS3Objects(date: Date): Seq[String] = {
    // We first retrieve a list of S3 filenames under our bucket prefix, then process.
    // See: https://tech.kinja.com/how-not-to-pull-from-s3-using-apache-spark-1704509219
    val request = new ListObjectsRequest()
    request.setBucketName(bucket)
    request.setPrefix(inputPath)

    AmazonS3ClientBuilder.defaultClient
      .listObjects(request)
      .getObjectSummaries
      .toList
      .map(_.getKey)
  }
}

final case class GCSStorageBackend(inputBucket: String, outputBucket: String, date: Date) extends StorageBackend {

  final val gcsInputDateFormatter = new java.text.SimpleDateFormat("yyyy-MM-dd")

  // Input files are expected to be in gs://<bucket>/2019-01-01-* format
  val inputPath: String = s"gs://$inputBucket/${gcsInputDateFormatter.format(date)}*"

  // Will write to gs://<outputBucket>/2019/01/01
  override def outputURI: String = s"gs://$outputBucket/${dateFormatter.format(date)}"

  override def ensureOutputEmpty(): Unit = {
    val storage = StorageOptions.getDefaultInstance.getService

    storage
      .list(outputBucket, BlobListOption.prefix(dateFormatter.format(date)))
      .iterateAll
      .foreach { blob =>
        storage.delete(blob.getBlobId)
      }
  }
}
