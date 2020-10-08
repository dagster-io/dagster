package io.dagster.events.models

import java.util.Date

import org.scalatest.{FlatSpec, Matchers}

class StorageBackendSpec extends FlatSpec with Matchers {
  val dateFormat = new java.text.SimpleDateFormat("yyyy-MM-dd")
  val date: Date = dateFormat.parse("2019-01-01")

  "LocalStorageBackend parse" should "match" in {
    val lsbe = LocalStorageBackend("base_path", date)

    assert(lsbe.inputPath === "base_path/raw/2019/01/01")
    assert(lsbe.outputPath === "base_path/output/2019/01/01")
  }

  "S3StorageBackend parse" should "match" in {
    val s3be = S3StorageBackend("bucket", "prefix", date)
    assert(s3be.inputPath === "prefix/raw/2019/01/01")
    assert(s3be.outputPath === "prefix/output/2019/01/01")
    assert(s3be.outputURI === "s3a://bucket/prefix/output/2019/01/01")
  }

  "GCSStorageBackend parse" should "match" in {
    val gcsbe = GCSStorageBackend("test", "test2", date)
    assert(gcsbe.outputURI === "gs://test2/2019/01/01")
  }
}
