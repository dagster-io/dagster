package org.examples;

import io.dagster.pipes.{
  DagsterPipesException, 
  PipesContext, 
  PipesSession
}
import io.dagster.pipes.loaders._
import io.dagster.pipes.writers._
import scala.math.random
import org.apache.spark.sql.SparkSession
import software.amazon.awssdk.services.s3.S3Client
import scala.collection.mutable
import scala.collection.JavaConverters._
import java.util.HashMap

object Example {

    def main(args: Array[String]): Unit = {
        val s3Client = S3Client.create()

        val paramsLoader = new PipesCliArgsParamsLoader(args)
        val contextLoader = new PipesS3ContextLoader(s3Client)
        val messageWriter = new PipesS3MessageWriter(s3Client)

        val session = new PipesSession(paramsLoader, contextLoader, messageWriter)

        session.runDagsterPipes(distributedCalculatePi)
    }

    // Based on the example at https://github.com/apache/spark/blob/master/examples/src/main/scala/org/apache/spark/examples/SparkPi.scala
    @throws[DagsterPipesException]
    private def distributedCalculatePi(context: PipesContext): Unit = {
        context.getLogger().info("This is a log message from scala to dagster")

        val spark = SparkSession
            .builder()
            .appName("Spark Pi")
            .getOrCreate()

        val slices = 2
        val n = math.min(100000L * slices, Int.MaxValue).toInt // avoid overflow
        val count = spark.sparkContext.parallelize(1 until n, slices).map { i =>
        val x = random() * 2 - 1
        val y = random() * 2 - 1
        if (x*x + y*y <= 1) 1 else 0
        }.reduce(_ + _)

        val pi = (4.0 * count / (n-1))
        spark.stop()

        context.getLogger().info(s"Succesfully used Spark to calculate pi! pi is approximately ${pi}")

        // Report whether the value of pi is between 3 and 4:
        context.reportAssetCheck(
            "demo_check", 
            pi < 4 && pi > 3, 
            mutable.Map.empty[String, Any].asJava, 
            null
        )

        val metaMap = mutable.Map("pi" -> pi.toFloat)
        context.reportAssetMaterialization(
            metaMap.asJava, 
            null, 
            null
        )
    }
}