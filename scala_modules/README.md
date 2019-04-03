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
