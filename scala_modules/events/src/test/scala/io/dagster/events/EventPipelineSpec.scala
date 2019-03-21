package io.dagster.events

import org.scalatest._

class EventPipelineSpec extends FlatSpec with Matchers {
  "The event pipeline" should "process events" in {
    // TODO
    //    val example = """{"environment": "production", "method": "GET", "cookies": {"session": "jJ01G0jq4HrW7vHiI0hLPg", "persistent": "9RX1m2vytWwj1bdrL_qDqA"}, "run_id": "039a684f-3c9e-44f9-8200-0679ed16b709", "type": "io.dagster.page_view", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36", "ip_address": "175.142.122.103", "timestamp": 1546419967.0, "url": "/search/category", "name": "Thomas Cameron", "email": "kbrooks@brown.com", "location": ["20.28527", "-103.42897", "Jocotepec", "MX", "America/Mexico_City"]}
    //                  """.stripMargin
    //
    //
    //    val json =
    //      """
    //        |{"location": [
    //        |    "20.28527",
    //        |    "-103.42897",
    //        |    "Jocotepec",
    //        |    "MX",
    //        |    "America/Mexico_City"
    //        |  ]
    //        |  }
    //      """.stripMargin

    //
    //    val doc = parse(json).getOrElse(Json.Null)
    //    val cursor = doc.hcursor
    //    cursor.downField("values").downField("qux").downArray

  }
}
