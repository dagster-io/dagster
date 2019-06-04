# Introduction
This project is our collection of Scala modules.

## Requirements
* IntelliJ IDEA
* IntelliJ Scalafmt Plugin 
* Scala 2.11
* Spark 2.4.0+

Spark is expected to be a provided dependency, so you should have a working Spark install somewhere, and `$SPARK_HOME` should be set in your environment.

You should use IntelliJ IDEA (CE is fine). We use the [scalafmt](https://scalameta.org/scalafmt/) IntelliJ IDEA plugin, configured to update on file save, and `scalastyle` 

Some editor config to put in place: [Case Class Definition Style](https://stackoverflow.com/a/26880974)

We follow the Twitter [Effective Scala](http://twitter.github.io/effectivescala/) style guide.

Saving this here for future reference: [Spark + S3](https://medium.com/@subhojit20_27731/apache-spark-and-amazon-s3-gotchas-and-best-practices-a767242f3d98)
 
### Installing scala and sbt on Mac OS X
Use homebrew:

    brew install scala@2.11
    brew install sbt

### References
* Spark + S3: http://deploymentzone.com/2015/12/20/s3a-on-spark-on-aws-ec2/
* Spark reading from S3: https://tech.kinja.com/how-not-to-pull-from-s3-using-apache-spark-1704509219
* Spark + GCS: https://stackoverflow.com/a/56400126/11295366

### Notes
Getting AWS S3 to play nice with Spark is complicated, because it involves a dependency on both aws-java-sdk and
hadoop-aws, and these two libraries need to be compatible versions (and compatible with Spark) or else everything
explodes:

https://hadoop.apache.org/docs/current/hadoop-aws/tools/hadoop-aws/index.html#Missing_method_in_com.amazonaws_class

We currently use AWS 1.7.4 and hadoop-aws 2.7.1 as these are known to be compatible and work with Spark 2.4.0+
