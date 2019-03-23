package io.dagster.events.models

import java.util.Date

sealed trait StorageBackend {
  final val inputPrefix = "raw"
  final val outputPrefix = "output"
  final val dateFormatter = new java.text.SimpleDateFormat("yyyy/MM/dd")

  def inputPath: String
  def outputPath: String

  protected def createFullPath(inputOrOutput: String): (String, Date) => String = (prefix, date) => {
    s"$prefix/$inputOrOutput/${dateFormatter.format(date)}"
  }
}

final case class LocalStorageBackend(path: String, date: Date) extends StorageBackend {
  override def inputPath: String = createFullPath(inputPrefix)(path, date)
  override def outputPath: String = createFullPath(outputPrefix)(path, date)
}

final case class S3StorageBackend(bucket: String, prefix: String, date: Date) extends StorageBackend {
  override def inputPath: String = createFullPath(inputPrefix)(prefix, date)
  override def outputPath: String = createFullPath(outputPrefix)(prefix, date)

  def outputURI: String = s"s3a://$bucket/$outputPath"
}
