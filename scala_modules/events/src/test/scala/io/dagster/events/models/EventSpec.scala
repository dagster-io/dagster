package io.dagster.events.models

import cats.syntax.either._
import io.circe._
import io.circe.parser._
import io.circe.generic.semiauto._
import org.scalatest.{FlatSpec, Matchers}

class EventSpec extends FlatSpec with Matchers {
  final lazy val eventCookies = EventCookies("jJ01G0jq4HrW7vHiI0hLPg", "9RX1m2vytWwj1bdrL_qDqA")
  final lazy val eventLocation = EventLocation(20.28527, -103.42897, "Jocotepec", "MX", "America/Mexico_City")
  final lazy val event = Event(
    "io.dagster.page_view",
    1546419967.0,
    "production",
    "GET",
    eventCookies,
    "039a684f-3c9e-44f9-8200-0679ed16b709",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
    "175.142.122.103",
    "/search/category",
    "Thomas Cameron",
    "kbrooks@brown.com",
    eventLocation
  )

  "EventLocation" should "parse" in {
        val json =
          """
            |[
            |  "20.28527",
            |  "-103.42897",
            |  "Jocotepec",
            |  "MX",
            |  "America/Mexico_City"
            |]
          """.stripMargin
    assert(EventLocation.fromString(json) === Some(eventLocation))
  }

  "EventCookies" should "parse" in {
    val json =
      """
        |{
        |  "session": "jJ01G0jq4HrW7vHiI0hLPg",
        |  "persistent": "9RX1m2vytWwj1bdrL_qDqA"
        |}
      """.stripMargin
    assert(EventCookies.fromString(json) === Some(eventCookies))
  }

  "Event" should "parse" in {
    val json = """
              |{
              |  "environment": "production",
              |  "method": "GET",
              |  "cookies": {
              |     "session": "jJ01G0jq4HrW7vHiI0hLPg",
              |     "persistent": "9RX1m2vytWwj1bdrL_qDqA"},
              |  "run_id": "039a684f-3c9e-44f9-8200-0679ed16b709",
              |  "type": "io.dagster.page_view",
              |  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
              |  "ip_address": "175.142.122.103",
              |  "timestamp": 1546419967.0,
              |  "url": "/search/category",
              |  "name": "Thomas Cameron",
              |  "email": "kbrooks@brown.com",
              |  "location": ["20.28527", "-103.42897", "Jocotepec", "MX", "America/Mexico_City"]
              |}
             """.stripMargin
    assert(Event.fromString(json) === Some(event))
  }
}
