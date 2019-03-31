package io.dagster.events.models

import cats.syntax.either._
import io.circe.{parser, Decoder, HCursor}
import io.circe.generic.semiauto.deriveDecoder

case class EventCookies(
  session: String,
  persistent: String
)

object EventCookies {
  implicit val decodeEventCookies: Decoder[EventCookies] = deriveDecoder[EventCookies]
  def fromString(a: String): Option[EventCookies] = parser.decode[EventCookies](a).toOption
}

case class EventLocation(
  latitude: Double,
  longitude: Double,
  city: String,
  country: String,
  region: String
)

object EventLocation {
  implicit val decodeEventLocation: Decoder[EventLocation] = new Decoder[EventLocation] {
    final def apply(c: HCursor): Decoder.Result[EventLocation] = {
      for {
        latitude  <- c.downArray.as[String].map(_.toDouble)
        longitude <- c.downArray.right.as[String].map(_.toDouble)
        city      <- c.downArray.right.right.as[String]
        country   <- c.downArray.right.right.right.as[String]
        region    <- c.downArray.right.right.right.right.as[String]
      } yield {
        EventLocation(latitude, longitude, city, country, region)
      }
    }
  }
  def fromString(a: String): Option[EventLocation] = parser.decode[EventLocation](a).toOption
}

case class Event(
  eventType: String,
  timestamp: Double,
  environment: String,
  method: String,
  cookies: EventCookies,
  runId: String,
  userAgent: String,
  ipAddress: String,
  url: String,
  name: String,
  email: String,
  location: EventLocation
)

object Event {
  import EventLocation._
  import EventCookies._

  implicit val decodeEvent: Decoder[Event] = new Decoder[Event] {
    final def apply(c: HCursor): Decoder.Result[Event] = {
      for {
        eventType   <- c.downField("type").as[String]
        timestamp   <- c.downField("timestamp").as[Double]
        environment <- c.downField("environment").as[String]
        method      <- c.downField("method").as[String]
        cookies     <- c.downField("cookies").as[EventCookies]
        runId       <- c.downField("run_id").as[String]
        userAgent   <- c.downField("user_agent").as[String]
        ipAddress   <- c.downField("ip_address").as[String]
        url         <- c.downField("url").as[String]
        name        <- c.downField("name").as[String]
        email       <- c.downField("email").as[String]
        location    <- c.downField("location").as[EventLocation]
      } yield {
        Event(
          eventType,
          timestamp,
          environment,
          method,
          cookies,
          runId,
          userAgent,
          ipAddress,
          url,
          name,
          email,
          location
        )
      }
    }
  }
  def fromString(a: String): Option[Event] = parser.decode[Event](a).toOption
}
