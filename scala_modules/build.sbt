import Dependencies._
import sbt.Keys.libraryDependencies

ThisBuild / scalaVersion     := "2.11.12"
ThisBuild / version          := "0.1.0-SNAPSHOT"
ThisBuild / organization     := "io.dagster"
ThisBuild / organizationName := "dagster"
ThisBuild / licenses         := List("Apache 2" -> new URL("http://www.apache.org/licenses/LICENSE-2.0.txt"))
ThisBuild / homepage         := Some(url("https://github.com/dagster-io/dagster"))

lazy val global = (project in file("."))
  .aggregate(
    events
  )

lazy val events = project
  .settings(
      name := "events",
      commonSettings
    )


lazy val commonSettings = Seq(
  libraryDependencies += scalaTest % Test,
  libraryDependencies ++= Seq(
    "org.apache.spark" %% "spark-core" % "2.4.0" % "provided",
    "org.apache.spark" %% "spark-sql" % "2.4.0" % "provided",
    "com.github.scopt" %% "scopt" % "4.0.0-RC2"
  )
)