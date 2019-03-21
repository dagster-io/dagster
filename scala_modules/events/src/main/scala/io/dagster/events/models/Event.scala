  package io.dagster.events.models

import java.net.InetAddress

  import cats.syntax.either._
  import io.circe._
  import io.circe.parser._
  import io.circe.generic.semiauto._


  case class EventCookies(
    session: String,
    persistent: String
  )

  case class EventLocation(
    latitude: Double,
    longitude: Double,
    city: String,
    country: String,
    region: String
  )

  case class Event(
    eventType: String,
    timestamp: Double,
    environment: String,
    method: String,
    cookies: EventCookies,
    runId: String,
    userAgent: String,
    ipAddress: java.net.InetAddress,
    url: String,
    name: String,
    email: String,
    location: EventLocation
  )


object Event {
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
  implicit val decodeEventCookies: Decoder[EventCookies] = deriveDecoder[EventCookies]
  implicit val decodeIPAddress: Decoder[java.net.InetAddress] = new Decoder[java.net.InetAddress] {
    final def apply(c: HCursor): Decoder.Result[java.net.InetAddress] = {
      for {
        ipAddress <- c.as[String]
      } yield {
        InetAddress.getByName(ipAddress)
      }
    }
  }

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
        ipAddress   <- c.downField("ip_address").as[java.net.InetAddress]
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

  def fromString(a: String): Option[Event] = {
      decode[Event](a).toOption
  }
}

