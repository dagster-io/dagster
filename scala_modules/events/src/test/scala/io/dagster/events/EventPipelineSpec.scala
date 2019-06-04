package io.dagster.events

import org.scalatest._

import scala.reflect.internal.FatalError

class EventPipelineSpec extends FlatSpec with Matchers {
  "The event pipeline" should "TODO process events" in {
    // TODO
  }

  "EventPipelineConfig: good arguments" should "be parsed correctly" in {
    EventPipelineConfig.parse(Array("--s3-bucket", "foo", "--s3-prefix", "bar", "--date", "2019-01-01"))
    EventPipelineConfig.parse(Array("--gcs-input-bucket", "foo", "--gcs-output-bucket", "bar", "--date", "2019-01-01"))
    EventPipelineConfig.parse(Array("--local-path", "foo", "--date", "2019-01-01"))
  }

  "EventPipelineConfig: bad arguments" should "fail to parse" in {
    val badArguments = Seq(
      // No date
      Array("--s3-bucket", "foo", "--s3-prefix", "bar"),
      // No prefix
      Array("--s3-bucket", "foo", "--date", "2019-01-01"),
      // Mixing AWS / GCP
      Array("--s3-bucket", "foo", "--s3-prefix", "bar", "--gcs-input-bucket", "foo", "--date", "2019-01-01"),
      // Mixing Local / AWS
      Array("--local-path", "foo", "--s3-bucket", "bar", "--date", "2019-01-01")
    )

    badArguments.foreach { bad =>
      val caught =
        intercept[FatalError] { EventPipelineConfig.parse(bad) }
      assert(caught.getMessage.contains("Incorrect options"))
    }
  }
}
