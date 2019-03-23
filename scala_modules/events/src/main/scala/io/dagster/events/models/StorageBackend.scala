package io.dagster.events.models

import java.util.Date
import java.io.File
import scala.reflect.io.Directory

sealed trait StorageBackend {
  final val inputPrefix = "raw"
  final val outputPrefix = "output"
  final val dateFormatter = new java.text.SimpleDateFormat("yyyy/MM/dd")

  def getInputPath(date: Date): String
  def getOutputPath(date: Date): String

  protected def createFullPath(inputOrOutput: String): (String, Date) => String = (prefix, date) => {
    s"$prefix/$inputOrOutput/${dateFormatter.format(date)}"
  }
}

final case class LocalStorageBackend(path: String) extends StorageBackend {
  override def getInputPath(date: Date): String = createFullPath(inputPrefix)(path, date)
  override def getOutputPath(date: Date): String = createFullPath(outputPrefix)(path, date)
}

final case class S3StorageBackend(bucket: String, prefix: String) extends StorageBackend {
  override def getInputPath(date: Date): String = createFullPath(inputPrefix)(prefix, date)
  override def getOutputPath(date: Date): String = createFullPath(outputPrefix)(prefix, date)
}
