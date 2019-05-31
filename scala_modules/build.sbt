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

lazy val circeVersion = "0.11.1"
lazy val awsVersion = "1.11.525"

lazy val events = project
  .settings(
    name := "events",
    assembly / assemblyMergeStrategy := {
      case x if x.endsWith("io.netty.versions.properties") => MergeStrategy.first
      case x =>
        val oldStrategy = (assemblyMergeStrategy in assembly).value
        oldStrategy(x)
    },
    // So, this is fun. Spark depends on hadoop-aws, which transitively depends on aws-java-sdk 1.7.4.
    // We want to use 1.11.525 because otherwise we have to explicitly handle the credentials chain in client code, and
    // We want to be use the default credentials chain provider.
    //
    // To make this version of the AWS jar available to this codebase, we shade it so that it does not conflict with the
    // version needed by Spark.
    //
    // These rules apply at jar assembly time, so code can still import com.amazonaws... as before.
    assembly / assemblyShadeRules := Seq(
      ShadeRule.rename("com.amazonaws.**" -> "shaded.com.amazonaws.@0").inAll,
      ShadeRule.rename("com.google.**" -> "shaded.com.google.@1").inAll
    ),

    assembly / assemblyExcludedJars := {
      val cp = (assembly / fullClasspath).value

      // See: https://github.com/milessabin/shapeless/wiki/Shapeless-with-SBT-Assembly-inside-Docker
      cp filter {_.data.getName == "shapeless_2.11-2.3.3.jar"}

      // This conflicts with the google-http-client provided by google-cloud-storage
      cp filter {_.data.getName == "google-http-client-apache-2.0.0.jar"}
    },
    resolvers += Resolver.sonatypeRepo("releases"),
      libraryDependencies ++= Seq(
      scalaTest          % Test,
      "org.apache.spark" %% "spark-core" % "2.4.0" % "provided",
      "org.apache.spark" %% "spark-sql" % "2.4.0" % "provided",
      "com.github.scopt" %% "scopt" % "4.0.0-RC2",
      "com.amazonaws"    % "aws-java-sdk" % awsVersion,
      "io.circe"         %% "circe-parser" % "0.11.1",
      "io.circe"         %% "circe-generic" % "0.11.1",
      "io.circe"         %% "circe-generic-extras" % "0.11.1",

      // Cloud Dataproc 1.4.x releases all use the 1.9.* gcs-connector, so we use it here. Also note that there's an
      // issue w/ the transitive dep on jmxtools so we exclude it.
      //
      // See:
      // * https://cloud.google.com/dataproc/docs/concepts/versioning/dataproc-release-1.4
      // * https://github.com/twitter-archive/cassie/issues/13#issuecomment-35681281
      // * http://bit.ly/2EXntNR
      "com.google.cloud.bigdataoss" % "gcs-connector" % "hadoop2-1.9.17"
        exclude("javax.jms", "jms")
        exclude("com.sun.jdmk", "jmxtools")
        exclude("com.sun.jmx", "jmxri"),

      "com.google.cloud" % "google-cloud-storage" % "1.76.0"
    ),
    scalacOptions ++= Seq("-Xmax-classfile-name", "240"),
    Compile / scalacOptions ++= Seq("-Xmax-classfile-name", "240")
  )
