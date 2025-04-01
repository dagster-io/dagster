"""NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT.

@generated

Produced via:
parse_spark_configs.py \

"""

from dagster import Bool, Field, Float, IntSource, Permissive, StringSource


def spark_config():
    return Field(
        Permissive(
            fields={
                "spark": Field(
                    Permissive(
                        fields={
                            "app": Field(
                                Permissive(
                                    fields={
                                        "name": Field(
                                            StringSource,
                                            description="""Application Properties: The name of your application. This will appear in the UI and in log data.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "driver": Field(
                                Permissive(
                                    fields={
                                        "cores": Field(
                                            IntSource,
                                            description="""Application Properties: Number of cores to use for the driver process, only in cluster mode.""",
                                            is_required=False,
                                        ),
                                        "maxResultSize": Field(
                                            StringSource,
                                            description="""Application Properties: Limit of total size of serialized results of all partitions for each Spark action (e.g. collect) in bytes. Should be at least 1M, or 0 for unlimited. Jobs will be aborted if the total size is above this limit. Having a high limit may cause out-of-memory errors in driver (depends on spark.driver.memory and memory overhead of objects in JVM). Setting a proper limit can protect the driver from out-of-memory errors.""",
                                            is_required=False,
                                        ),
                                        "memory": Field(
                                            StringSource,
                                            description="""Application Properties: Amount of memory to use for the driver process, i.e. where SparkContext is initialized, in the same format as JVM memory strings with a size unit suffix ("k", "m", "g" or "t") (e.g. 512m, 2g). Note: In client mode, this config must not be set through the SparkConf directly in your application, because the driver JVM has already started at that point. Instead, please set this through the --driver-memory command line option or in your default properties file.""",
                                            is_required=False,
                                        ),
                                        "memoryOverhead": Field(
                                            StringSource,
                                            description="""Application Properties: Amount of non-heap memory to be allocated per driver process in cluster mode, in MiB unless otherwise specified. This is memory that accounts for things like VM overheads, interned strings, other native overheads, etc. This tends to grow with the container size (typically 6-10%). This option is currently supported on YARN, Mesos and Kubernetes. Note: Non-heap memory includes off-heap memory (when spark.memory.offHeap.enabled=true) and memory used by other driver processes (e.g. python process that goes with a PySpark driver) and memory used by other non-driver processes running in the same container. The maximum memory size of container to running driver is determined by the sum of spark.driver.memoryOverhead and spark.driver.memory.""",
                                            is_required=False,
                                        ),
                                        "memoryOverheadFactor": Field(
                                            StringSource,
                                            description="""Application Properties: Fraction of driver memory to be allocated as additional non-heap memory per driver process in cluster mode. This is memory that accounts for things like VM overheads, interned strings, other native overheads, etc. This tends to grow with the container size. This value defaults to 0.10 except for Kubernetes non-JVM jobs, which defaults to 0.40. This is done as non-JVM tasks need more non-JVM heap space and such tasks commonly fail with "Memory Overhead Exceeded" errors. This preempts this error with a higher default. This value is ignored if spark.driver.memoryOverhead is set directly.""",
                                            is_required=False,
                                        ),
                                        "resource": Field(
                                            Permissive(
                                                fields={
                                                    "{resourceName}": Field(
                                                        Permissive(
                                                            fields={
                                                                "amount": Field(
                                                                    StringSource,
                                                                    description="""Application Properties: Amount of a particular resource type to use on the driver. If this is used, you must also specify the spark.driver.resource.{resourceName}.discoveryScript for the driver to find the resource on startup.""",
                                                                    is_required=False,
                                                                ),
                                                                "discoveryScript": Field(
                                                                    StringSource,
                                                                    description="""Application Properties: A script for the driver to run to discover a particular resource type. This should write to STDOUT a JSON string in the format of the ResourceInformation class. This has a name and an array of addresses. For a client-submitted driver, discovery script must assign different resource addresses to this driver comparing to other drivers on the same host.""",
                                                                    is_required=False,
                                                                ),
                                                                "vendor": Field(
                                                                    StringSource,
                                                                    description="""Application Properties: Vendor of the resources to use for the driver. This option is currently only supported on Kubernetes and is actually both the vendor and domain following the Kubernetes device plugin naming convention. (e.g. For GPUs on Kubernetes this config would be set to nvidia.com or amd.com)""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        "supervise": Field(
                                            Bool,
                                            description="""Application Properties: If true, restarts the driver automatically if it fails with a non-zero exit status. Only has effect in Spark standalone mode or Mesos cluster deploy mode.""",
                                            is_required=False,
                                        ),
                                        "log": Field(
                                            Permissive(
                                                fields={
                                                    "dfsDir": Field(
                                                        StringSource,
                                                        description="""Application Properties: Base directory in which Spark driver logs are synced, if spark.driver.log.persistToDfs.enabled is true. Within this base directory, each application logs the driver logs to an application specific file. Users may want to set this to a unified location like an HDFS directory so driver log files can be persisted for later usage. This directory should allow any Spark user to read/write files and the Spark History Server user to delete files. Additionally, older logs from this directory are cleaned by the Spark History Server if spark.history.fs.driverlog.cleaner.enabled is true and, if they are older than max age configured by setting spark.history.fs.driverlog.cleaner.maxAge.""",
                                                        is_required=False,
                                                    ),
                                                    "persistToDfs": Field(
                                                        Permissive(
                                                            fields={
                                                                "enabled": Field(
                                                                    StringSource,
                                                                    description="""Application Properties: If true, spark application running in client mode will write driver logs to a persistent storage, configured in spark.driver.log.dfsDir. If spark.driver.log.dfsDir is not configured, driver logs will not be persisted. Additionally, enable the cleaner by setting spark.history.fs.driverlog.cleaner.enabled to true in Spark History Server.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                    "layout": Field(
                                                        StringSource,
                                                        description="""Application Properties: The layout for the driver logs that are synced to spark.driver.log.dfsDir. If this is not configured, it uses the layout for the first appender defined in log4j2.properties. If that is also not configured, driver logs use the default layout.""",
                                                        is_required=False,
                                                    ),
                                                    "allowErasureCoding": Field(
                                                        StringSource,
                                                        description="""Application Properties: Whether to allow driver logs to use erasure coding. On HDFS, erasure coded files will not update as quickly as regular replicated files, so they make take longer to reflect changes written by the application. Note that even if this is true, Spark will still not force the file to use erasure coding, it will simply use file system defaults.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "extraClassPath": Field(
                                            StringSource,
                                            description="""Runtime Environment: Extra classpath entries to prepend to the classpath of the driver. Note: In client mode, this config must not be set through the SparkConf directly in your application, because the driver JVM has already started at that point. Instead, please set this through the --driver-class-path command line option or in your default properties file.""",
                                            is_required=False,
                                        ),
                                        "defaultJavaOptions": Field(
                                            StringSource,
                                            description="""Runtime Environment: A string of default JVM options to prepend to spark.driver.extraJavaOptions. This is intended to be set by administrators. For instance, GC settings or other logging. Note that it is illegal to set maximum heap size (-Xmx) settings with this option. Maximum heap size settings can be set with spark.driver.memory in the cluster mode and through the --driver-memory command line option in the client mode. Note: In client mode, this config must not be set through the SparkConf directly in your application, because the driver JVM has already started at that point. Instead, please set this through the --driver-java-options command line option or in your default properties file.""",
                                            is_required=False,
                                        ),
                                        "extraJavaOptions": Field(
                                            StringSource,
                                            description="""Runtime Environment: A string of extra JVM options to pass to the driver. This is intended to be set by users. For instance, GC settings or other logging. Note that it is illegal to set maximum heap size (-Xmx) settings with this option. Maximum heap size settings can be set with spark.driver.memory in the cluster mode and through the --driver-memory command line option in the client mode. Note: In client mode, this config must not be set through the SparkConf directly in your application, because the driver JVM has already started at that point. Instead, please set this through the --driver-java-options command line option or in your default properties file. spark.driver.defaultJavaOptions will be prepended to this configuration.""",
                                            is_required=False,
                                        ),
                                        "extraLibraryPath": Field(
                                            StringSource,
                                            description="""Runtime Environment: Set a special library path to use when launching the driver JVM. Note: In client mode, this config must not be set through the SparkConf directly in your application, because the driver JVM has already started at that point. Instead, please set this through the --driver-library-path command line option or in your default properties file.""",
                                            is_required=False,
                                        ),
                                        "userClassPathFirst": Field(
                                            Bool,
                                            description="""Runtime Environment: (Experimental) Whether to give user-added jars precedence over Spark's own jars when loading classes in the driver. This feature can be used to mitigate conflicts between Spark's dependencies and user dependencies. It is currently an experimental feature. This is used in cluster mode only.""",
                                            is_required=False,
                                        ),
                                        "blockManager": Field(
                                            Permissive(
                                                fields={
                                                    "port": Field(
                                                        StringSource,
                                                        description="""Networking: Driver-specific port for the block manager to listen on, for cases where it cannot use the same configuration as executors.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "bindAddress": Field(
                                            StringSource,
                                            description="""Networking: Hostname or IP address where to bind listening sockets. This config overrides the SPARK_LOCAL_IP environment variable (see below). It also allows a different address from the local one to be advertised to executors or external systems. This is useful, for example, when running containers with bridged networking. For this to properly work, the different ports used by the driver (RPC, block manager and UI) need to be forwarded from the container's host.""",
                                            is_required=False,
                                        ),
                                        "host": Field(
                                            StringSource,
                                            description="""Networking: Hostname or IP address for the driver. This is used for communicating with the executors and the standalone Master.""",
                                            is_required=False,
                                        ),
                                        "port": Field(
                                            StringSource,
                                            description="""Networking: Port for the driver to listen on. This is used for communicating with the executors and the standalone Master.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "resources": Field(
                                Permissive(
                                    fields={
                                        "discoveryPlugin": Field(
                                            StringSource,
                                            description="""Application Properties: Comma-separated list of class names implementing org.apache.spark.api.resource.ResourceDiscoveryPlugin to load into the application. This is for advanced users to replace the resource discovery class with a custom implementation. Spark will try each class specified until one of them returns the resource information for that resource. It tries the discovery script last if none of the plugins return information for that resource.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "executor": Field(
                                Permissive(
                                    fields={
                                        "memory": Field(
                                            StringSource,
                                            description="""Application Properties: Amount of memory to use per executor process, in the same format as JVM memory strings with a size unit suffix ("k", "m", "g" or "t") (e.g. 512m, 2g).""",
                                            is_required=False,
                                        ),
                                        "pyspark": Field(
                                            Permissive(
                                                fields={
                                                    "memory": Field(
                                                        StringSource,
                                                        description="""Application Properties: The amount of memory to be allocated to PySpark in each executor, in MiB unless otherwise specified. If set, PySpark memory for an executor will be limited to this amount. If not set, Spark will not limit Python's memory use and it is up to the application to avoid exceeding the overhead memory space shared with other non-JVM processes. When PySpark is run in YARN or Kubernetes, this memory is added to executor resource requests. Note: This feature is dependent on Python's `resource` module; therefore, the behaviors and limitations are inherited. For instance, Windows does not support resource limiting and actual resource is not limited on MacOS.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "memoryOverhead": Field(
                                            StringSource,
                                            description="""Application Properties: Amount of additional memory to be allocated per executor process, in MiB unless otherwise specified. This is memory that accounts for things like VM overheads, interned strings, other native overheads, etc. This tends to grow with the executor size (typically 6-10%). This option is currently supported on YARN and Kubernetes. Note: Additional memory includes PySpark executor memory (when spark.executor.pyspark.memory is not configured) and memory used by other non-executor processes running in the same container. The maximum memory size of container to running executor is determined by the sum of spark.executor.memoryOverhead, spark.executor.memory, spark.memory.offHeap.size and spark.executor.pyspark.memory.""",
                                            is_required=False,
                                        ),
                                        "memoryOverheadFactor": Field(
                                            StringSource,
                                            description="""Application Properties: Fraction of executor memory to be allocated as additional non-heap memory per executor process. This is memory that accounts for things like VM overheads, interned strings, other native overheads, etc. This tends to grow with the container size. This value defaults to 0.10 except for Kubernetes non-JVM jobs, which defaults to 0.40. This is done as non-JVM tasks need more non-JVM heap space and such tasks commonly fail with "Memory Overhead Exceeded" errors. This preempts this error with a higher default. This value is ignored if spark.executor.memoryOverhead is set directly.""",
                                            is_required=False,
                                        ),
                                        "resource": Field(
                                            Permissive(
                                                fields={
                                                    "{resourceName}": Field(
                                                        Permissive(
                                                            fields={
                                                                "amount": Field(
                                                                    StringSource,
                                                                    description="""Application Properties: Amount of a particular resource type to use per executor process. If this is used, you must also specify the spark.executor.resource.{resourceName}.discoveryScript for the executor to find the resource on startup.""",
                                                                    is_required=False,
                                                                ),
                                                                "discoveryScript": Field(
                                                                    StringSource,
                                                                    description="""Application Properties: A script for the executor to run to discover a particular resource type. This should write to STDOUT a JSON string in the format of the ResourceInformation class. This has a name and an array of addresses.""",
                                                                    is_required=False,
                                                                ),
                                                                "vendor": Field(
                                                                    StringSource,
                                                                    description="""Application Properties: Vendor of the resources to use for the executors. This option is currently only supported on Kubernetes and is actually both the vendor and domain following the Kubernetes device plugin naming convention. (e.g. For GPUs on Kubernetes this config would be set to nvidia.com or amd.com)""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        "decommission": Field(
                                            Permissive(
                                                fields={
                                                    "killInterval": Field(
                                                        StringSource,
                                                        description="""Application Properties: Duration after which a decommissioned executor will be killed forcefully by an outside (e.g. non-spark) service.""",
                                                        is_required=False,
                                                    ),
                                                    "forceKillTimeout": Field(
                                                        StringSource,
                                                        description="""Application Properties: Duration after which a Spark will force a decommissioning executor to exit. This should be set to a high value in most situations as low values will prevent block migrations from having enough time to complete.""",
                                                        is_required=False,
                                                    ),
                                                    "signal": Field(
                                                        StringSource,
                                                        description="""Application Properties: The signal that used to trigger the executor to start decommission.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "maxNumFailures": Field(
                                            StringSource,
                                            description="""Application Properties: The maximum number of executor failures before failing the application. This configuration only takes effect on YARN, or Kubernetes when `spark.kubernetes.allocation.pods.allocator` is set to 'direct'.""",
                                            is_required=False,
                                        ),
                                        "failuresValidityInterval": Field(
                                            StringSource,
                                            description="""Application Properties: Interval after which executor failures will be considered independent and not accumulate towards the attempt count. This configuration only takes effect on YARN, or Kubernetes when `spark.kubernetes.allocation.pods.allocator` is set to 'direct'.""",
                                            is_required=False,
                                        ),
                                        "extraClassPath": Field(
                                            StringSource,
                                            description="""Runtime Environment: Extra classpath entries to prepend to the classpath of executors. This exists primarily for backwards-compatibility with older versions of Spark. Users typically should not need to set this option.""",
                                            is_required=False,
                                        ),
                                        "defaultJavaOptions": Field(
                                            StringSource,
                                            description="""Runtime Environment: A string of default JVM options to prepend to spark.executor.extraJavaOptions. This is intended to be set by administrators. For instance, GC settings or other logging. Note that it is illegal to set Spark properties or maximum heap size (-Xmx) settings with this option. Spark properties should be set using a SparkConf object or the spark-defaults.conf file used with the spark-submit script. Maximum heap size settings can be set with spark.executor.memory. The following symbols, if present will be interpolated: {{APP_ID}} will be replaced by application ID and {{EXECUTOR_ID}} will be replaced by executor ID. For example, to enable verbose gc logging to a file named for the executor ID of the app in /tmp, pass a 'value' of: -verbose:gc -Xloggc:/tmp/{{APP_ID}}-{{EXECUTOR_ID}}.gc""",
                                            is_required=False,
                                        ),
                                        "extraJavaOptions": Field(
                                            StringSource,
                                            description="""Runtime Environment: A string of extra JVM options to pass to executors. This is intended to be set by users. For instance, GC settings or other logging. Note that it is illegal to set Spark properties or maximum heap size (-Xmx) settings with this option. Spark properties should be set using a SparkConf object or the spark-defaults.conf file used with the spark-submit script. Maximum heap size settings can be set with spark.executor.memory. The following symbols, if present will be interpolated: {{APP_ID}} will be replaced by application ID and {{EXECUTOR_ID}} will be replaced by executor ID. For example, to enable verbose gc logging to a file named for the executor ID of the app in /tmp, pass a 'value' of: -verbose:gc -Xloggc:/tmp/{{APP_ID}}-{{EXECUTOR_ID}}.gc spark.executor.defaultJavaOptions will be prepended to this configuration.""",
                                            is_required=False,
                                        ),
                                        "extraLibraryPath": Field(
                                            StringSource,
                                            description="""Runtime Environment: Set a special library path to use when launching executor JVM's.""",
                                            is_required=False,
                                        ),
                                        "logs": Field(
                                            Permissive(
                                                fields={
                                                    "rolling": Field(
                                                        Permissive(
                                                            fields={
                                                                "maxRetainedFiles": Field(
                                                                    IntSource,
                                                                    description="""Runtime Environment: Sets the number of latest rolling log files that are going to be retained by the system. Older log files will be deleted. Disabled by default.""",
                                                                    is_required=False,
                                                                ),
                                                                "enableCompression": Field(
                                                                    Bool,
                                                                    description="""Runtime Environment: Enable executor log compression. If it is enabled, the rolled executor logs will be compressed. Disabled by default.""",
                                                                    is_required=False,
                                                                ),
                                                                "maxSize": Field(
                                                                    IntSource,
                                                                    description="""Runtime Environment: Set the max size of the file in bytes by which the executor logs will be rolled over. Rolling is disabled by default. See spark.executor.logs.rolling.maxRetainedFiles for automatic cleaning of old logs.""",
                                                                    is_required=False,
                                                                ),
                                                                "strategy": Field(
                                                                    StringSource,
                                                                    description="""Runtime Environment: Set the strategy of rolling of executor logs. By default it is disabled. It can be set to "time" (time-based rolling) or "size" (size-based rolling). For "time", use spark.executor.logs.rolling.time.interval to set the rolling interval. For "size", use spark.executor.logs.rolling.maxSize to set the maximum file size for rolling.""",
                                                                    is_required=False,
                                                                ),
                                                                "time": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "interval": Field(
                                                                                StringSource,
                                                                                description="""Runtime Environment: Set the time interval by which the executor logs will be rolled over. Rolling is disabled by default. Valid values are daily, hourly, minutely or any interval in seconds. See spark.executor.logs.rolling.maxRetainedFiles for automatic cleaning of old logs.""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        "userClassPathFirst": Field(
                                            Bool,
                                            description="""Runtime Environment: (Experimental) Same functionality as spark.driver.userClassPathFirst, but applied to executor instances.""",
                                            is_required=False,
                                        ),
                                        "cores": Field(
                                            IntSource,
                                            description="""Execution Behavior: The number of cores to use on each executor. In standalone and Mesos coarse-grained modes, for more detail, see this description.""",
                                            is_required=False,
                                        ),
                                        "heartbeatInterval": Field(
                                            StringSource,
                                            description="""Execution Behavior: Interval between each executor's heartbeats to the driver. Heartbeats let the driver know that the executor is still alive and update it with metrics for in-progress tasks. spark.executor.heartbeatInterval should be significantly less than spark.network.timeout""",
                                            is_required=False,
                                        ),
                                        "processTreeMetrics": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        StringSource,
                                                        description="""Executor Metrics: Whether to collect process tree metrics (from the /proc filesystem) when collecting executor metrics. Note: The process tree metrics are collected only if the /proc filesystem exists.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "metrics": Field(
                                            Permissive(
                                                fields={
                                                    "pollingInterval": Field(
                                                        StringSource,
                                                        description="""Executor Metrics: How often to collect executor metrics (in milliseconds). If 0, the polling is done on executor heartbeats (thus at the heartbeat interval, specified by spark.executor.heartbeatInterval). If positive, the polling is done at this interval.""",
                                                        is_required=False,
                                                    ),
                                                    "fileSystemSchemes": Field(
                                                        StringSource,
                                                        description="""Executor Metrics: The file system schemes to report in executor metrics.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "extraListeners": Field(
                                StringSource,
                                description="""Application Properties: A comma-separated list of classes that implement SparkListener; when initializing SparkContext, instances of these classes will be created and registered with Spark's listener bus. If a class has a single-argument constructor that accepts a SparkConf, that constructor will be called; otherwise, a zero-argument constructor will be called. If no valid constructor can be found, the SparkContext creation will fail with an exception.""",
                                is_required=False,
                            ),
                            "local": Field(
                                Permissive(
                                    fields={
                                        "dir": Field(
                                            StringSource,
                                            description="""Application Properties: Directory to use for "scratch" space in Spark, including map output files and RDDs that get stored on disk. This should be on a fast, local disk in your system. It can also be a comma-separated list of multiple directories on different disks. Note: This will be overridden by SPARK_LOCAL_DIRS (Standalone), MESOS_SANDBOX (Mesos) or LOCAL_DIRS (YARN) environment variables set by the cluster manager.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "logConf": Field(
                                Bool,
                                description="""Application Properties: Logs the effective SparkConf as INFO when a SparkContext is started.""",
                                is_required=False,
                            ),
                            "master": Field(
                                StringSource,
                                description="""Application Properties: The cluster manager to connect to. See the list of allowed master URL's.""",
                                is_required=False,
                            ),
                            "submit": Field(
                                Permissive(
                                    fields={
                                        "deployMode": Field(
                                            StringSource,
                                            description="""Application Properties: The deploy mode of Spark driver program, either "client" or "cluster", Which means to launch driver program locally ("client") or remotely ("cluster") on one of the nodes inside the cluster.""",
                                            is_required=False,
                                        ),
                                        "pyFiles": Field(
                                            StringSource,
                                            description="""Runtime Environment: Comma-separated list of .zip, .egg, or .py files to place on the PYTHONPATH for Python apps. Globs are allowed.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "log": Field(
                                Permissive(
                                    fields={
                                        "callerContext": Field(
                                            StringSource,
                                            description="""Application Properties: Application information that will be written into Yarn RM log/HDFS audit log when running on Yarn/HDFS. Its length depends on the Hadoop configuration hadoop.caller.context.max.size. It should be concise, and typically can have up to 50 characters.""",
                                            is_required=False,
                                        ),
                                        "level": Field(
                                            StringSource,
                                            description="""Application Properties: When set, overrides any user-defined log settings as if calling SparkContext.setLogLevel() at Spark startup. Valid log levels include: "ALL", "DEBUG", "ERROR", "FATAL", "INFO", "OFF", "TRACE", "WARN".""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "decommission": Field(
                                Permissive(
                                    fields={
                                        "enabled": Field(
                                            StringSource,
                                            description="""Application Properties: When decommission enabled, Spark will try its best to shut down the executor gracefully. Spark will try to migrate all the RDD blocks (controlled by spark.storage.decommission.rddBlocks.enabled) and shuffle blocks (controlled by spark.storage.decommission.shuffleBlocks.enabled) from the decommissioning executor to a remote executor when spark.storage.decommission.enabled is enabled. With decommission enabled, Spark will also decommission an executor instead of killing when spark.dynamicAllocation.enabled enabled.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "redaction": Field(
                                Permissive(
                                    fields={
                                        "regex": Field(
                                            StringSource,
                                            description="""Runtime Environment: Regex to decide which Spark configuration properties and environment variables in driver and executor environments contain sensitive information. When this regex matches a property key or value, the value is redacted from the environment UI and various logs like YARN and event logs.""",
                                            is_required=False,
                                        ),
                                        "string": Field(
                                            Permissive(
                                                fields={
                                                    "regex": Field(
                                                        StringSource,
                                                        description="""Runtime Environment: Regex to decide which parts of strings produced by Spark contain sensitive information. When this regex matches a string part, that string part is replaced by a dummy value. This is currently used to redact the output of SQL explain commands.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "python": Field(
                                Permissive(
                                    fields={
                                        "profile": Field(
                                            Permissive(
                                                fields={
                                                    "root": Field(
                                                        Bool,
                                                        description="""Runtime Environment: Enable profiling in Python worker, the profile result will show up by sc.show_profiles(), or it will be displayed before the driver exits. It also can be dumped into disk by sc.dump_profiles(path). If some of the profile results had been displayed manually, they will not be displayed automatically before driver exiting. By default the pyspark.profiler.BasicProfiler will be used, but this can be overridden by passing a profiler class in as a parameter to the SparkContext constructor.""",
                                                        is_required=False,
                                                    ),
                                                    "dump": Field(
                                                        StringSource,
                                                        description="""Runtime Environment: The directory which is used to dump the profile result before driver exiting. The results will be dumped as separated file for each RDD. They can be loaded by pstats.Stats(). If this is specified, the profile result will not be displayed automatically.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "worker": Field(
                                            Permissive(
                                                fields={
                                                    "memory": Field(
                                                        StringSource,
                                                        description="""Runtime Environment: Amount of memory to use per python worker process during aggregation, in the same format as JVM memory strings with a size unit suffix ("k", "m", "g" or "t") (e.g. 512m, 2g). If the memory used during aggregation goes above this amount, it will spill the data into disks.""",
                                                        is_required=False,
                                                    ),
                                                    "reuse": Field(
                                                        Bool,
                                                        description="""Runtime Environment: Reuse Python worker or not. If yes, it will use a fixed number of Python workers, does not need to fork() a Python process for every task. It will be very useful if there is a large broadcast, then the broadcast will not need to be transferred from JVM to Python worker for every task.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "files": Field(
                                Permissive(
                                    fields={
                                        "root": Field(
                                            StringSource,
                                            description="""Runtime Environment: Comma-separated list of files to be placed in the working directory of each executor. Globs are allowed.""",
                                            is_required=False,
                                        ),
                                        "io": Field(
                                            Permissive(
                                                fields={
                                                    "connectionTimeout": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: Timeout for the established connections for fetching files in Spark RPC environments to be marked as idled and closed if there are still outstanding files being downloaded but no traffic no the channel for at least `connectionTimeout`.""",
                                                        is_required=False,
                                                    ),
                                                    "connectionCreationTimeout": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: Timeout for establishing a connection for fetching files in Spark RPC environments.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "fetchTimeout": Field(
                                            StringSource,
                                            description="""Execution Behavior: Communication timeout to use when fetching files added through SparkContext.addFile() from the driver.""",
                                            is_required=False,
                                        ),
                                        "useFetchCache": Field(
                                            Bool,
                                            description="""Execution Behavior: If set to true (default), file fetching will use a local cache that is shared by executors that belong to the same application, which can improve task launching performance when running many executors on the same host. If set to false, these caching optimizations will be disabled and all executors will fetch their own copies of files. This optimization may be disabled in order to use Spark local directories that reside on NFS filesystems (see SPARK-6313 for more details).""",
                                            is_required=False,
                                        ),
                                        "overwrite": Field(
                                            Bool,
                                            description="""Execution Behavior: Whether to overwrite any files which exist at the startup. Users can not overwrite the files added by SparkContext.addFile or SparkContext.addJar before even if this option is set true.""",
                                            is_required=False,
                                        ),
                                        "ignoreCorruptFiles": Field(
                                            StringSource,
                                            description="""Execution Behavior: Whether to ignore corrupt files. If true, the Spark jobs will continue to run when encountering corrupted or non-existing files and contents that have been read will still be returned.""",
                                            is_required=False,
                                        ),
                                        "ignoreMissingFiles": Field(
                                            StringSource,
                                            description="""Execution Behavior: Whether to ignore missing files. If true, the Spark jobs will continue to run when encountering missing files and the contents that have been read will still be returned.""",
                                            is_required=False,
                                        ),
                                        "maxPartitionBytes": Field(
                                            IntSource,
                                            description="""Execution Behavior: The maximum number of bytes to pack into a single partition when reading files.""",
                                            is_required=False,
                                        ),
                                        "openCostInBytes": Field(
                                            IntSource,
                                            description="""Execution Behavior: The estimated cost to open a file, measured by the number of bytes could be scanned at the same time. This is used when putting multiple files into a partition. It is better to overestimate, then the partitions with small files will be faster than partitions with bigger files.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "jars": Field(
                                Permissive(
                                    fields={
                                        "root": Field(
                                            StringSource,
                                            description="""Runtime Environment: Comma-separated list of jars to include on the driver and executor classpaths. Globs are allowed.""",
                                            is_required=False,
                                        ),
                                        "packages": Field(
                                            StringSource,
                                            description="""Runtime Environment: Comma-separated list of Maven coordinates of jars to include on the driver and executor classpaths. The coordinates should be groupId:artifactId:version. If spark.jars.ivySettings is given artifacts will be resolved according to the configuration in the file, otherwise artifacts will be searched for in the local maven repo, then maven central and finally any additional remote repositories given by the command-line option --repositories. For more details, see Advanced Dependency Management.""",
                                            is_required=False,
                                        ),
                                        "excludes": Field(
                                            StringSource,
                                            description="""Runtime Environment: Comma-separated list of groupId:artifactId, to exclude while resolving the dependencies provided in spark.jars.packages to avoid dependency conflicts.""",
                                            is_required=False,
                                        ),
                                        "ivy": Field(
                                            StringSource,
                                            description="""Runtime Environment: Path to specify the Ivy user directory, used for the local Ivy cache and package files from spark.jars.packages. This will override the Ivy property ivy.default.ivy.user.dir which defaults to ~/.ivy2.""",
                                            is_required=False,
                                        ),
                                        "ivySettings": Field(
                                            StringSource,
                                            description="""Runtime Environment: Path to an Ivy settings file to customize resolution of jars specified using spark.jars.packages instead of the built-in defaults, such as maven central. Additional repositories given by the command-line option --repositories or spark.jars.repositories will also be included. Useful for allowing Spark to resolve artifacts from behind a firewall e.g. via an in-house artifact server like Artifactory. Details on the settings file format can be found at Settings Files. Only paths with file:// scheme are supported. Paths without a scheme are assumed to have a file:// scheme. When running in YARN cluster mode, this file will also be localized to the remote driver for dependency resolution within SparkContext#addJar""",
                                            is_required=False,
                                        ),
                                        "repositories": Field(
                                            StringSource,
                                            description="""Runtime Environment: Comma-separated list of additional remote repositories to search for the maven coordinates given with --packages or spark.jars.packages.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "archives": Field(
                                StringSource,
                                description="""Runtime Environment: Comma-separated list of archives to be extracted into the working directory of each executor. .jar, .tar.gz, .tgz and .zip are supported. You can specify the directory name to unpack via adding # after the file name to unpack, for example, file.zip#directory. This configuration is experimental.""",
                                is_required=False,
                            ),
                            "pyspark": Field(
                                Permissive(
                                    fields={
                                        "driver": Field(
                                            Permissive(
                                                fields={
                                                    "python": Field(
                                                        StringSource,
                                                        description="""Runtime Environment: Python binary executable to use for PySpark in driver. (default is spark.pyspark.python)""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "python": Field(
                                            StringSource,
                                            description="""Runtime Environment: Python binary executable to use for PySpark in both driver and executors.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "reducer": Field(
                                Permissive(
                                    fields={
                                        "maxSizeInFlight": Field(
                                            StringSource,
                                            description="""Shuffle Behavior: Maximum size of map outputs to fetch simultaneously from each reduce task, in MiB unless otherwise specified. Since each output requires us to create a buffer to receive it, this represents a fixed memory overhead per reduce task, so keep it small unless you have a large amount of memory.""",
                                            is_required=False,
                                        ),
                                        "maxReqsInFlight": Field(
                                            IntSource,
                                            description="""Shuffle Behavior: This configuration limits the number of remote requests to fetch blocks at any given point. When the number of hosts in the cluster increase, it might lead to very large number of inbound connections to one or more nodes, causing the workers to fail under load. By allowing it to limit the number of fetch requests, this scenario can be mitigated.""",
                                            is_required=False,
                                        ),
                                        "maxBlocksInFlightPerAddress": Field(
                                            IntSource,
                                            description="""Shuffle Behavior: This configuration limits the number of remote blocks being fetched per reduce task from a given host port. When a large number of blocks are being requested from a given address in a single fetch or simultaneously, this could crash the serving executor or Node Manager. This is especially useful to reduce the load on the Node Manager when external shuffle is enabled. You can mitigate this issue by setting it to a lower value.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "shuffle": Field(
                                Permissive(
                                    fields={
                                        "compress": Field(
                                            Bool,
                                            description="""Shuffle Behavior: Whether to compress map output files. Generally a good idea. Compression will use spark.io.compression.codec.""",
                                            is_required=False,
                                        ),
                                        "file": Field(
                                            Permissive(
                                                fields={
                                                    "buffer": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: Size of the in-memory buffer for each shuffle file output stream, in KiB unless otherwise specified. These buffers reduce the number of disk seeks and system calls made in creating intermediate shuffle files.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "unsafe": Field(
                                            Permissive(
                                                fields={
                                                    "file": Field(
                                                        Permissive(
                                                            fields={
                                                                "output": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "buffer": Field(
                                                                                StringSource,
                                                                                description="""Shuffle Behavior: The file system for this buffer size after each partition is written in unsafe shuffle writer. In KiB unless otherwise specified.""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        "spill": Field(
                                            Permissive(
                                                fields={
                                                    "diskWriteBufferSize": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: The buffer size, in bytes, to use when writing the sorted records to an on-disk file.""",
                                                        is_required=False,
                                                    ),
                                                    "compress": Field(
                                                        Bool,
                                                        description="""Shuffle Behavior: Whether to compress data spilled during shuffles. Compression will use spark.io.compression.codec.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "io": Field(
                                            Permissive(
                                                fields={
                                                    "maxRetries": Field(
                                                        IntSource,
                                                        description="""Shuffle Behavior: (Netty only) Fetches that fail due to IO-related exceptions are automatically retried if this is set to a non-zero value. This retry logic helps stabilize large shuffles in the face of long GC pauses or transient network connectivity issues.""",
                                                        is_required=False,
                                                    ),
                                                    "numConnectionsPerPeer": Field(
                                                        IntSource,
                                                        description="""Shuffle Behavior: (Netty only) Connections between hosts are reused in order to reduce connection buildup for large clusters. For clusters with many hard disks and few hosts, this may result in insufficient concurrency to saturate all disks, and so users may consider increasing this value.""",
                                                        is_required=False,
                                                    ),
                                                    "preferDirectBufs": Field(
                                                        Bool,
                                                        description="""Shuffle Behavior: (Netty only) Off-heap buffers are used to reduce garbage collection during shuffle and cache block transfer. For environments where off-heap memory is tightly limited, users may wish to turn this off to force all allocations from Netty to be on-heap.""",
                                                        is_required=False,
                                                    ),
                                                    "retryWait": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: (Netty only) How long to wait between retries of fetches. The maximum delay caused by retrying is 15 seconds by default, calculated as maxRetries * retryWait.""",
                                                        is_required=False,
                                                    ),
                                                    "backLog": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: Length of the accept queue for the shuffle service. For large applications, this value may need to be increased, so that incoming connections are not dropped if the service cannot keep up with a large number of connections arriving in a short period of time. This needs to be configured wherever the shuffle service itself is running, which may be outside of the application (see spark.shuffle.service.enabled option below). If set below 1, will fallback to OS default defined by Netty's io.netty.util.NetUtil#SOMAXCONN.""",
                                                        is_required=False,
                                                    ),
                                                    "connectionTimeout": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: Timeout for the established connections between shuffle servers and clients to be marked as idled and closed if there are still outstanding fetch requests but no traffic no the channel for at least `connectionTimeout`.""",
                                                        is_required=False,
                                                    ),
                                                    "connectionCreationTimeout": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: Timeout for establishing a connection between the shuffle servers and clients.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "service": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        Bool,
                                                        description="""Shuffle Behavior: Enables the external shuffle service. This service preserves the shuffle files written by executors e.g. so that executors can be safely removed, or so that shuffle fetches can continue in the event of executor failure. The external shuffle service must be set up in order to enable it. See dynamic allocation configuration and setup documentation for more information.""",
                                                        is_required=False,
                                                    ),
                                                    "port": Field(
                                                        IntSource,
                                                        description="""Shuffle Behavior: Port on which the external shuffle service will run.""",
                                                        is_required=False,
                                                    ),
                                                    "name": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: The configured name of the Spark shuffle service the client should communicate with. This must match the name used to configure the Shuffle within the YARN NodeManager configuration (yarn.nodemanager.aux-services). Only takes effect when spark.shuffle.service.enabled is set to true.""",
                                                        is_required=False,
                                                    ),
                                                    "index": Field(
                                                        Permissive(
                                                            fields={
                                                                "cache": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "size": Field(
                                                                                StringSource,
                                                                                description="""Shuffle Behavior: Cache entries limited to the specified memory footprint, in bytes unless otherwise specified.""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                    "removeShuffle": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: Whether to use the ExternalShuffleService for deleting shuffle blocks for deallocated executors when the shuffle is no longer needed. Without this enabled, shuffle data on executors that are deallocated will remain on disk until the application ends.""",
                                                        is_required=False,
                                                    ),
                                                    "fetch": Field(
                                                        Permissive(
                                                            fields={
                                                                "rdd": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "enabled": Field(
                                                                                StringSource,
                                                                                description="""Shuffle Behavior: Whether to use the ExternalShuffleService for fetching disk persisted RDD blocks. In case of dynamic allocation if this feature is enabled executors having only disk persisted blocks are considered idle after spark.dynamicAllocation.executorIdleTimeout and will be released accordingly.""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                    "db": Field(
                                                        Permissive(
                                                            fields={
                                                                "enabled": Field(
                                                                    StringSource,
                                                                    description="""Shuffle Behavior: Whether to use db in ExternalShuffleService. Note that this only affects standalone mode.""",
                                                                    is_required=False,
                                                                ),
                                                                "backend": Field(
                                                                    StringSource,
                                                                    description="""Shuffle Behavior: Specifies a disk-based store used in shuffle service local db. Setting as LEVELDB or ROCKSDB.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        "maxChunksBeingTransferred": Field(
                                            IntSource,
                                            description="""Shuffle Behavior: The max number of chunks allowed to be transferred at the same time on shuffle service. Note that new incoming connections will be closed when the max number is hit. The client will retry according to the shuffle retry configs (see spark.shuffle.io.maxRetries and spark.shuffle.io.retryWait), if those limits are reached the task will fail with fetch failure.""",
                                            is_required=False,
                                        ),
                                        "sort": Field(
                                            Permissive(
                                                fields={
                                                    "bypassMergeThreshold": Field(
                                                        IntSource,
                                                        description="""Shuffle Behavior: (Advanced) In the sort-based shuffle manager, avoid merge-sorting data if there is no map-side aggregation and there are at most this many reduce partitions.""",
                                                        is_required=False,
                                                    ),
                                                    "io": Field(
                                                        Permissive(
                                                            fields={
                                                                "plugin": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "class": Field(
                                                                                StringSource,
                                                                                description="""Shuffle Behavior: Name of the class to use for shuffle IO.""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        "accurateBlockThreshold": Field(
                                            IntSource,
                                            description="""Shuffle Behavior: Threshold in bytes above which the size of shuffle blocks in HighlyCompressedMapStatus is accurately recorded. This helps to prevent OOM by avoiding underestimating shuffle block size when fetch shuffle blocks.""",
                                            is_required=False,
                                        ),
                                        "registration": Field(
                                            Permissive(
                                                fields={
                                                    "timeout": Field(
                                                        IntSource,
                                                        description="""Shuffle Behavior: Timeout in milliseconds for registration to the external shuffle service.""",
                                                        is_required=False,
                                                    ),
                                                    "maxAttempts": Field(
                                                        IntSource,
                                                        description="""Shuffle Behavior: When we fail to register to the external shuffle service, we will retry for maxAttempts times.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "reduceLocality": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: Whether to compute locality preferences for reduce tasks.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "mapOutput": Field(
                                            Permissive(
                                                fields={
                                                    "minSizeForBroadcast": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: The size at which we use Broadcast to send the map output statuses to the executors.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "detectCorrupt": Field(
                                            Permissive(
                                                fields={
                                                    "root": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: Whether to detect any corruption in fetched blocks.""",
                                                        is_required=False,
                                                    ),
                                                    "useExtraMemory": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: If enabled, part of a compressed/encrypted stream will be de-compressed/de-crypted by using extra memory to detect early corruption. Any IOException thrown will cause the task to be retried once and if it fails again with same exception, then FetchFailedException will be thrown to retry previous stage.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "useOldFetchProtocol": Field(
                                            StringSource,
                                            description="""Shuffle Behavior: Whether to use the old protocol while doing the shuffle block fetching. It is only enabled while we need the compatibility in the scenario of new Spark version job fetching shuffle blocks from old version external shuffle service.""",
                                            is_required=False,
                                        ),
                                        "readHostLocalDisk": Field(
                                            StringSource,
                                            description="""Shuffle Behavior: If enabled (and spark.shuffle.useOldFetchProtocol is disabled, shuffle blocks requested from those block managers which are running on the same host are read from the disk directly instead of being fetched as remote blocks over the network.""",
                                            is_required=False,
                                        ),
                                        "checksum": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: Whether to calculate the checksum of shuffle data. If enabled, Spark will calculate the checksum values for each partition data within the map output file and store the values in a checksum file on the disk. When there's shuffle data corruption detected, Spark will try to diagnose the cause (e.g., network issue, disk issue, etc.) of the corruption by using the checksum file.""",
                                                        is_required=False,
                                                    ),
                                                    "algorithm": Field(
                                                        StringSource,
                                                        description="""Shuffle Behavior: The algorithm is used to calculate the shuffle checksum. Currently, it only supports built-in algorithms of JDK, e.g., ADLER32, CRC32.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "eventLog": Field(
                                Permissive(
                                    fields={
                                        "logBlockUpdates": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        StringSource,
                                                        description="""Spark UI: Whether to log events for every block update, if spark.eventLog.enabled is true. *Warning*: This will increase the size of the event log considerably.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "longForm": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        StringSource,
                                                        description="""Spark UI: If true, use the long form of call sites in the event log. Otherwise use the short form.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "compress": Field(
                                            StringSource,
                                            description="""Spark UI: Whether to compress logged events, if spark.eventLog.enabled is true.""",
                                            is_required=False,
                                        ),
                                        "compression": Field(
                                            Permissive(
                                                fields={
                                                    "codec": Field(
                                                        StringSource,
                                                        description="""Spark UI: The codec to compress logged events. By default, Spark provides four codecs: lz4, lzf, snappy, and zstd. You can also use fully qualified class names to specify the codec, e.g. org.apache.spark.io.LZ4CompressionCodec, org.apache.spark.io.LZFCompressionCodec, org.apache.spark.io.SnappyCompressionCodec, and org.apache.spark.io.ZStdCompressionCodec.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "erasureCoding": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        StringSource,
                                                        description="""Spark UI: Whether to allow event logs to use erasure coding, or turn erasure coding off, regardless of filesystem defaults. On HDFS, erasure coded files will not update as quickly as regular replicated files, so the application updates will take longer to appear in the History Server. Note that even if this is true, Spark will still not force the file to use erasure coding, it will simply use filesystem defaults.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "dir": Field(
                                            StringSource,
                                            description="""Spark UI: Base directory in which Spark events are logged, if spark.eventLog.enabled is true. Within this base directory, Spark creates a sub-directory for each application, and logs the events specific to the application in this directory. Users may want to set this to a unified location like an HDFS directory so history files can be read by the history server.""",
                                            is_required=False,
                                        ),
                                        "enabled": Field(
                                            StringSource,
                                            description="""Spark UI: Whether to log Spark events, useful for reconstructing the Web UI after the application has finished.""",
                                            is_required=False,
                                        ),
                                        "overwrite": Field(
                                            StringSource,
                                            description="""Spark UI: Whether to overwrite any existing files.""",
                                            is_required=False,
                                        ),
                                        "buffer": Field(
                                            Permissive(
                                                fields={
                                                    "kb": Field(
                                                        StringSource,
                                                        description="""Spark UI: Buffer size to use when writing to output streams, in KiB unless otherwise specified.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "rolling": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        StringSource,
                                                        description="""Spark UI: Whether rolling over event log files is enabled. If set to true, it cuts down each event log file to the configured size.""",
                                                        is_required=False,
                                                    ),
                                                    "maxFileSize": Field(
                                                        StringSource,
                                                        description="""Spark UI: When spark.eventLog.rolling.enabled=true, specifies the max size of event log file before it's rolled over.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "logStageExecutorMetrics": Field(
                                            StringSource,
                                            description="""Executor Metrics: Whether to write per-stage peaks of executor metrics (for each executor) to the event log. Note: The metrics are polled (collected) and sent in the executor heartbeat, and this is always done; this configuration is only to determine if aggregated metric peaks are written to the event log.""",
                                            is_required=False,
                                        ),
                                        "gcMetrics": Field(
                                            Permissive(
                                                fields={
                                                    "youngGenerationGarbageCollectors": Field(
                                                        StringSource,
                                                        description="""Executor Metrics: Names of supported young generation garbage collector. A name usually is the return of GarbageCollectorMXBean.getName. The built-in young generation garbage collectors are Copy,PS Scavenge,ParNew,G1 Young Generation.""",
                                                        is_required=False,
                                                    ),
                                                    "oldGenerationGarbageCollectors": Field(
                                                        StringSource,
                                                        description="""Executor Metrics: Names of supported old generation garbage collector. A name usually is the return of GarbageCollectorMXBean.getName. The built-in old generation garbage collectors are MarkSweepCompact,PS MarkSweep,ConcurrentMarkSweep,G1 Old Generation.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "ui": Field(
                                Permissive(
                                    fields={
                                        "dagGraph": Field(
                                            Permissive(
                                                fields={
                                                    "retainedRootRDDs": Field(
                                                        StringSource,
                                                        description="""Spark UI: How many DAG graph nodes the Spark UI and status APIs remember before garbage collecting.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "enabled": Field(
                                            StringSource,
                                            description="""Spark UI: Whether to run the web UI for the Spark application.""",
                                            is_required=False,
                                        ),
                                        "store": Field(
                                            Permissive(
                                                fields={
                                                    "path": Field(
                                                        StringSource,
                                                        description="""Spark UI: Local directory where to cache application information for live UI. By default this is not set, meaning all application information will be kept in memory.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "killEnabled": Field(
                                            StringSource,
                                            description="""Spark UI: Allows jobs and stages to be killed from the web UI.""",
                                            is_required=False,
                                        ),
                                        "liveUpdate": Field(
                                            Permissive(
                                                fields={
                                                    "period": Field(
                                                        StringSource,
                                                        description="""Spark UI: How often to update live entities. -1 means "never update" when replaying applications, meaning only the last write will happen. For live applications, this avoids a few operations that we can live without when rapidly processing incoming task events.""",
                                                        is_required=False,
                                                    ),
                                                    "minFlushPeriod": Field(
                                                        StringSource,
                                                        description="""Spark UI: Minimum time elapsed before stale UI data is flushed. This avoids UI staleness when incoming task events are not fired frequently.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "port": Field(
                                            StringSource,
                                            description="""Spark UI: Port for your application's dashboard, which shows memory and workload data.""",
                                            is_required=False,
                                        ),
                                        "retainedJobs": Field(
                                            StringSource,
                                            description="""Spark UI: How many jobs the Spark UI and status APIs remember before garbage collecting. This is a target maximum, and fewer elements may be retained in some circumstances.""",
                                            is_required=False,
                                        ),
                                        "retainedStages": Field(
                                            StringSource,
                                            description="""Spark UI: How many stages the Spark UI and status APIs remember before garbage collecting. This is a target maximum, and fewer elements may be retained in some circumstances.""",
                                            is_required=False,
                                        ),
                                        "retainedTasks": Field(
                                            StringSource,
                                            description="""Spark UI: How many tasks in one stage the Spark UI and status APIs remember before garbage collecting. This is a target maximum, and fewer elements may be retained in some circumstances.""",
                                            is_required=False,
                                        ),
                                        "reverseProxy": Field(
                                            StringSource,
                                            description="""Spark UI: Enable running Spark Master as reverse proxy for worker and application UIs. In this mode, Spark master will reverse proxy the worker and application UIs to enable access without requiring direct access to their hosts. Use it with caution, as worker and application UI will not be accessible directly, you will only be able to access them through spark master/proxy public URL. This setting affects all the workers and application UIs running in the cluster and must be set on all the workers, drivers and masters.""",
                                            is_required=False,
                                        ),
                                        "reverseProxyUrl": Field(
                                            StringSource,
                                            description="""Spark UI: If the Spark UI should be served through another front-end reverse proxy, this is the URL for accessing the Spark master UI through that reverse proxy. This is useful when running proxy for authentication e.g. an OAuth proxy. The URL may contain a path prefix, like http://mydomain.com/path/to/spark/, allowing you to serve the UI for multiple Spark clusters and other web applications through the same virtual host and port. Normally, this should be an absolute URL including scheme (http/https), host and port. It is possible to specify a relative URL starting with "/" here. In this case, all URLs generated by the Spark UI and Spark REST APIs will be server-relative links -- this will still work, as the entire Spark UI is served through the same host and port. The setting affects link generation in the Spark UI, but the front-end reverse proxy is responsible for stripping a path prefix before forwarding the request, rewriting redirects which point directly to the Spark master, redirecting access from http://mydomain.com/path/to/spark to http://mydomain.com/path/to/spark/ (trailing slash after path prefix); otherwise relative links on the master page do not work correctly. This setting affects all the workers and application UIs running in the cluster and must be set identically on all the workers, drivers and masters. In is only effective when spark.ui.reverseProxy is turned on. This setting is not needed when the Spark master web UI is directly reachable. Note that the value of the setting can't contain the keyword `proxy` or `history` after split by "/". Spark UI relies on both keywords for getting REST API endpoints from URIs.""",
                                            is_required=False,
                                        ),
                                        "proxyRedirectUri": Field(
                                            StringSource,
                                            description="""Spark UI: Where to address redirects when Spark is running behind a proxy. This will make Spark modify redirect responses so they point to the proxy server, instead of the Spark UI's own address. This should be only the address of the server, without any prefix paths for the application; the prefix should be set either by the proxy server itself (by adding the X-Forwarded-Context request header), or by setting the proxy base in the Spark app's configuration.""",
                                            is_required=False,
                                        ),
                                        "showConsoleProgress": Field(
                                            StringSource,
                                            description="""Spark UI: Show the progress bar in the console. The progress bar shows the progress of stages that run for longer than 500ms. If multiple stages run at the same time, multiple progress bars will be displayed on the same line. Note: In shell environment, the default value of spark.ui.showConsoleProgress is true.""",
                                            is_required=False,
                                        ),
                                        "custom": Field(
                                            Permissive(
                                                fields={
                                                    "executor": Field(
                                                        Permissive(
                                                            fields={
                                                                "log": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "url": Field(
                                                                                StringSource,
                                                                                description="""Spark UI: Specifies custom spark executor log URL for supporting external log service instead of using cluster managers' application log URLs in Spark UI. Spark will support some path variables via patterns which can vary on cluster manager. Please check the documentation for your cluster manager to see which patterns are supported, if any. Please note that this configuration also replaces original log urls in event log, which will be also effective when accessing the application on history server. The new log urls must be permanent, otherwise you might have dead link for executor log urls. For now, only YARN and K8s cluster manager supports this configuration""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        "retainedDeadExecutors": Field(
                                            StringSource,
                                            description="""Spark UI: How many dead executors the Spark UI and status APIs remember before garbage collecting.""",
                                            is_required=False,
                                        ),
                                        "filters": Field(
                                            StringSource,
                                            description="""Spark UI: Comma separated list of filter class names to apply to the Spark Web UI. The filter should be a standard javax servlet Filter. Filter parameters can also be specified in the configuration, by setting config entries of the form spark.<class name of filter>.param.<param name>=<value> For example: spark.ui.filters=com.test.filter1 spark.com.test.filter1.param.name1=foo spark.com.test.filter1.param.name2=bar""",
                                            is_required=False,
                                        ),
                                        "requestHeaderSize": Field(
                                            StringSource,
                                            description="""Spark UI: The maximum allowed size for a HTTP request header, in bytes unless otherwise specified. This setting applies for the Spark History Server too.""",
                                            is_required=False,
                                        ),
                                        "timelineEnabled": Field(
                                            StringSource,
                                            description="""Spark UI: Whether to display event timeline data on UI pages.""",
                                            is_required=False,
                                        ),
                                        "timeline": Field(
                                            Permissive(
                                                fields={
                                                    "executors": Field(
                                                        Permissive(
                                                            fields={
                                                                "maximum": Field(
                                                                    StringSource,
                                                                    description="""Spark UI: The maximum number of executors shown in the event timeline.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                    "jobs": Field(
                                                        Permissive(
                                                            fields={
                                                                "maximum": Field(
                                                                    StringSource,
                                                                    description="""Spark UI: The maximum number of jobs shown in the event timeline.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                    "stages": Field(
                                                        Permissive(
                                                            fields={
                                                                "maximum": Field(
                                                                    StringSource,
                                                                    description="""Spark UI: The maximum number of stages shown in the event timeline.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                    "tasks": Field(
                                                        Permissive(
                                                            fields={
                                                                "maximum": Field(
                                                                    StringSource,
                                                                    description="""Spark UI: The maximum number of tasks shown in the event timeline.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "worker": Field(
                                Permissive(
                                    fields={
                                        "ui": Field(
                                            Permissive(
                                                fields={
                                                    "retainedExecutors": Field(
                                                        StringSource,
                                                        description="""Spark UI: How many finished executors the Spark UI and status APIs remember before garbage collecting.""",
                                                        is_required=False,
                                                    ),
                                                    "retainedDrivers": Field(
                                                        StringSource,
                                                        description="""Spark UI: How many finished drivers the Spark UI and status APIs remember before garbage collecting.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "sql": Field(
                                Permissive(
                                    fields={
                                        "ui": Field(
                                            Permissive(
                                                fields={
                                                    "retainedExecutions": Field(
                                                        StringSource,
                                                        description="""Spark UI: How many finished executions the Spark UI and status APIs remember before garbage collecting.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "streaming": Field(
                                Permissive(
                                    fields={
                                        "ui": Field(
                                            Permissive(
                                                fields={
                                                    "retainedBatches": Field(
                                                        StringSource,
                                                        description="""Spark Streaming: How many batches the Spark Streaming UI and status APIs remember before garbage collecting.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "backpressure": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        StringSource,
                                                        description="""Spark Streaming: Enables or disables Spark Streaming's internal backpressure mechanism (since 1.5). This enables the Spark Streaming to control the receiving rate based on the current batch scheduling delays and processing times so that the system receives only as fast as the system can process. Internally, this dynamically sets the maximum receiving rate of receivers. This rate is upper bounded by the values spark.streaming.receiver.maxRate and spark.streaming.kafka.maxRatePerPartition if they are set (see below).""",
                                                        is_required=False,
                                                    ),
                                                    "initialRate": Field(
                                                        StringSource,
                                                        description="""Spark Streaming: This is the initial maximum receiving rate at which each receiver will receive data for the first batch when the backpressure mechanism is enabled.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "blockInterval": Field(
                                            StringSource,
                                            description="""Spark Streaming: Interval at which data received by Spark Streaming receivers is chunked into blocks of data before storing them in Spark. Minimum recommended - 50 ms. See the performance tuning section in the Spark Streaming programming guide for more details.""",
                                            is_required=False,
                                        ),
                                        "receiver": Field(
                                            Permissive(
                                                fields={
                                                    "maxRate": Field(
                                                        StringSource,
                                                        description="""Spark Streaming: Maximum rate (number of records per second) at which each receiver will receive data. Effectively, each stream will consume at most this number of records per second. Setting this configuration to 0 or a negative number will put no limit on the rate. See the deployment guide in the Spark Streaming programming guide for mode details.""",
                                                        is_required=False,
                                                    ),
                                                    "writeAheadLog": Field(
                                                        Permissive(
                                                            fields={
                                                                "enable": Field(
                                                                    StringSource,
                                                                    description="""Spark Streaming: Enable write-ahead logs for receivers. All the input data received through receivers will be saved to write-ahead logs that will allow it to be recovered after driver failures. See the deployment guide in the Spark Streaming programming guide for more details.""",
                                                                    is_required=False,
                                                                ),
                                                                "closeFileAfterWrite": Field(
                                                                    StringSource,
                                                                    description="""Spark Streaming: Whether to close the file after writing a write-ahead log record on the receivers. Set this to 'true' when you want to use S3 (or any file system that does not support flushing) for the data WAL on the receivers.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        "unpersist": Field(
                                            StringSource,
                                            description="""Spark Streaming: Force RDDs generated and persisted by Spark Streaming to be automatically unpersisted from Spark's memory. The raw input data received by Spark Streaming is also automatically cleared. Setting this to false will allow the raw data and persisted RDDs to be accessible outside the streaming application as they will not be cleared automatically. But it comes at the cost of higher memory usage in Spark.""",
                                            is_required=False,
                                        ),
                                        "stopGracefullyOnShutdown": Field(
                                            StringSource,
                                            description="""Spark Streaming: If true, Spark shuts down the StreamingContext gracefully on JVM shutdown rather than immediately.""",
                                            is_required=False,
                                        ),
                                        "kafka": Field(
                                            Permissive(
                                                fields={
                                                    "maxRatePerPartition": Field(
                                                        StringSource,
                                                        description="""Spark Streaming: Maximum rate (number of records per second) at which data will be read from each Kafka partition when using the new Kafka direct stream API. See the Kafka Integration guide for more details.""",
                                                        is_required=False,
                                                    ),
                                                    "minRatePerPartition": Field(
                                                        StringSource,
                                                        description="""Spark Streaming: Minimum rate (number of records per second) at which data will be read from each Kafka partition when using the new Kafka direct stream API.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "driver": Field(
                                            Permissive(
                                                fields={
                                                    "writeAheadLog": Field(
                                                        Permissive(
                                                            fields={
                                                                "closeFileAfterWrite": Field(
                                                                    StringSource,
                                                                    description="""Spark Streaming: Whether to close the file after writing a write-ahead log record on the driver. Set this to 'true' when you want to use S3 (or any file system that does not support flushing) for the metadata WAL on the driver.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "appStatusStore": Field(
                                Permissive(
                                    fields={
                                        "diskStoreDir": Field(
                                            StringSource,
                                            description="""Spark UI: Local directory where to store diagnostic information of SQL executions. This configuration is only for live UI.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "broadcast": Field(
                                Permissive(
                                    fields={
                                        "compress": Field(
                                            StringSource,
                                            description="""Compression and Serialization: Whether to compress broadcast variables before sending them. Generally a good idea. Compression will use spark.io.compression.codec.""",
                                            is_required=False,
                                        ),
                                        "blockSize": Field(
                                            StringSource,
                                            description="""Execution Behavior: Size of each piece of a block for TorrentBroadcastFactory, in KiB unless otherwise specified. Too large a value decreases parallelism during broadcast (makes it slower); however, if it is too small, BlockManager might take a performance hit.""",
                                            is_required=False,
                                        ),
                                        "checksum": Field(
                                            StringSource,
                                            description="""Execution Behavior: Whether to enable checksum for broadcast. If enabled, broadcasts will include a checksum, which can help detect corrupted blocks, at the cost of computing and sending a little more data. It's possible to disable it if the network has other mechanisms to guarantee data won't be corrupted during broadcast.""",
                                            is_required=False,
                                        ),
                                        "UDFCompressionThreshold": Field(
                                            StringSource,
                                            description="""Execution Behavior: The threshold at which user-defined functions (UDFs) and Python RDD commands are compressed by broadcast in bytes unless otherwise specified.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "checkpoint": Field(
                                Permissive(
                                    fields={
                                        "compress": Field(
                                            StringSource,
                                            description="""Compression and Serialization: Whether to compress RDD checkpoints. Generally a good idea. Compression will use spark.io.compression.codec.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "io": Field(
                                Permissive(
                                    fields={
                                        "compression": Field(
                                            Permissive(
                                                fields={
                                                    "codec": Field(
                                                        StringSource,
                                                        description="""Compression and Serialization: The codec used to compress internal data such as RDD partitions, event log, broadcast variables and shuffle outputs. By default, Spark provides four codecs: lz4, lzf, snappy, and zstd. You can also use fully qualified class names to specify the codec, e.g. org.apache.spark.io.LZ4CompressionCodec, org.apache.spark.io.LZFCompressionCodec, org.apache.spark.io.SnappyCompressionCodec, and org.apache.spark.io.ZStdCompressionCodec.""",
                                                        is_required=False,
                                                    ),
                                                    "lz4": Field(
                                                        Permissive(
                                                            fields={
                                                                "blockSize": Field(
                                                                    StringSource,
                                                                    description="""Compression and Serialization: Block size used in LZ4 compression, in the case when LZ4 compression codec is used. Lowering this block size will also lower shuffle memory usage when LZ4 is used. Default unit is bytes, unless otherwise specified. This configuration only applies to `spark.io.compression.codec`.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                    "snappy": Field(
                                                        Permissive(
                                                            fields={
                                                                "blockSize": Field(
                                                                    StringSource,
                                                                    description="""Compression and Serialization: Block size in Snappy compression, in the case when Snappy compression codec is used. Lowering this block size will also lower shuffle memory usage when Snappy is used. Default unit is bytes, unless otherwise specified. This configuration only applies to `spark.io.compression.codec`.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                    "zstd": Field(
                                                        Permissive(
                                                            fields={
                                                                "level": Field(
                                                                    StringSource,
                                                                    description="""Compression and Serialization: Compression level for Zstd compression codec. Increasing the compression level will result in better compression at the expense of more CPU and memory. This configuration only applies to `spark.io.compression.codec`.""",
                                                                    is_required=False,
                                                                ),
                                                                "bufferSize": Field(
                                                                    StringSource,
                                                                    description="""Compression and Serialization: Buffer size in bytes used in Zstd compression, in the case when Zstd compression codec is used. Lowering this size will lower the shuffle memory usage when Zstd is used, but it might increase the compression cost because of excessive JNI call overhead. This configuration only applies to `spark.io.compression.codec`.""",
                                                                    is_required=False,
                                                                ),
                                                                "bufferPool": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "enabled": Field(
                                                                                StringSource,
                                                                                description="""Compression and Serialization: If true, enable buffer pool of ZSTD JNI library.""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "kryo": Field(
                                Permissive(
                                    fields={
                                        "classesToRegister": Field(
                                            StringSource,
                                            description="""Compression and Serialization: If you use Kryo serialization, give a comma-separated list of custom class names to register with Kryo. See the tuning guide for more details.""",
                                            is_required=False,
                                        ),
                                        "referenceTracking": Field(
                                            StringSource,
                                            description="""Compression and Serialization: Whether to track references to the same object when serializing data with Kryo, which is necessary if your object graphs have loops and useful for efficiency if they contain multiple copies of the same object. Can be disabled to improve performance if you know this is not the case.""",
                                            is_required=False,
                                        ),
                                        "registrationRequired": Field(
                                            StringSource,
                                            description="""Compression and Serialization: Whether to require registration with Kryo. If set to 'true', Kryo will throw an exception if an unregistered class is serialized. If set to false (the default), Kryo will write unregistered class names along with each object. Writing class names can cause significant performance overhead, so enabling this option can enforce strictly that a user has not omitted classes from registration.""",
                                            is_required=False,
                                        ),
                                        "registrator": Field(
                                            StringSource,
                                            description="""Compression and Serialization: If you use Kryo serialization, give a comma-separated list of classes that register your custom classes with Kryo. This property is useful if you need to register your classes in a custom way, e.g. to specify a custom field serializer. Otherwise spark.kryo.classesToRegister is simpler. It should be set to classes that extend KryoRegistrator. See the tuning guide for more details.""",
                                            is_required=False,
                                        ),
                                        "unsafe": Field(
                                            StringSource,
                                            description="""Compression and Serialization: Whether to use unsafe based Kryo serializer. Can be substantially faster by using Unsafe Based IO.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "kryoserializer": Field(
                                Permissive(
                                    fields={
                                        "buffer": Field(
                                            Permissive(
                                                fields={
                                                    "root": Field(
                                                        StringSource,
                                                        description="""Compression and Serialization: Initial size of Kryo's serialization buffer, in KiB unless otherwise specified. Note that there will be one buffer per core on each worker. This buffer will grow up to spark.kryoserializer.buffer.max if needed.""",
                                                        is_required=False,
                                                    ),
                                                    "max": Field(
                                                        StringSource,
                                                        description="""Compression and Serialization: Maximum allowable size of Kryo serialization buffer, in MiB unless otherwise specified. This must be larger than any object you attempt to serialize and must be less than 2048m. Increase this if you get a "buffer limit exceeded" exception inside Kryo.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "rdd": Field(
                                Permissive(
                                    fields={
                                        "compress": Field(
                                            StringSource,
                                            description="""Compression and Serialization: Whether to compress serialized RDD partitions (e.g. for StorageLevel.MEMORY_ONLY_SER in Java and Scala or StorageLevel.MEMORY_ONLY in Python). Can save substantial space at the cost of some extra CPU time. Compression will use spark.io.compression.codec.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "serializer": Field(
                                Permissive(
                                    fields={
                                        "root": Field(
                                            StringSource,
                                            description="""Compression and Serialization: Class to use for serializing objects that will be sent over the network or need to be cached in serialized form. The default of Java serialization works with any Serializable Java object but is quite slow, so we recommend using org.apache.spark.serializer.KryoSerializer and configuring Kryo serialization when speed is necessary. Can be any subclass of org.apache.spark.Serializer.""",
                                            is_required=False,
                                        ),
                                        "objectStreamReset": Field(
                                            StringSource,
                                            description="""Compression and Serialization: When serializing using org.apache.spark.serializer.JavaSerializer, the serializer caches objects to prevent writing redundant data, however that stops garbage collection of those objects. By calling 'reset' you flush that info from the serializer, and allow old objects to be collected. To turn off this periodic reset set it to -1. By default it will reset the serializer every 100 objects.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "memory": Field(
                                Permissive(
                                    fields={
                                        "fraction": Field(
                                            Float,
                                            description="""Memory Management: Fraction of (heap space - 300MB) used for execution and storage. The lower this is, the more frequently spills and cached data eviction occur. The purpose of this config is to set aside memory for internal metadata, user data structures, and imprecise size estimation in the case of sparse, unusually large records. Leaving this at the default value is recommended. For more detail, including important information about correctly tuning JVM garbage collection when increasing this value, see this description.""",
                                            is_required=False,
                                        ),
                                        "storageFraction": Field(
                                            Float,
                                            description="""Memory Management: Amount of storage memory immune to eviction, expressed as a fraction of the size of the region set aside by spark.memory.fraction. The higher this is, the less working memory may be available to execution and tasks may spill to disk more often. Leaving this at the default value is recommended. For more detail, see this description.""",
                                            is_required=False,
                                        ),
                                        "offHeap": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        Bool,
                                                        description="""Memory Management: If true, Spark will attempt to use off-heap memory for certain operations. If off-heap memory use is enabled, then spark.memory.offHeap.size must be positive.""",
                                                        is_required=False,
                                                    ),
                                                    "size": Field(
                                                        IntSource,
                                                        description="""Memory Management: The absolute amount of memory which can be used for off-heap allocation, in bytes unless otherwise specified. This setting has no impact on heap memory usage, so if your executors' total memory consumption must fit within some hard limit then be sure to shrink your JVM heap size accordingly. This must be set to a positive value when spark.memory.offHeap.enabled=true.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "storage": Field(
                                Permissive(
                                    fields={
                                        "unrollMemoryThreshold": Field(
                                            StringSource,
                                            description="""Memory Management: Initial memory to request before unrolling any block.""",
                                            is_required=False,
                                        ),
                                        "replication": Field(
                                            Permissive(
                                                fields={
                                                    "proactive": Field(
                                                        Bool,
                                                        description="""Memory Management: Enables proactive block replication for RDD blocks. Cached RDD block replicas lost due to executor failures are replenished if there are any existing available replicas. This tries to get the replication level of the block to the initial number.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "localDiskByExecutors": Field(
                                            Permissive(
                                                fields={
                                                    "cacheSize": Field(
                                                        StringSource,
                                                        description="""Memory Management: The max number of executors for which the local dirs are stored. This size is both applied for the driver and both for the executors side to avoid having an unbounded store. This cache will be used to avoid the network in case of fetching disk persisted RDD blocks or shuffle blocks (when spark.shuffle.readHostLocalDisk is set) from the same host.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "memoryMapThreshold": Field(
                                            StringSource,
                                            description="""Execution Behavior: Size of a block above which Spark memory maps when reading a block from disk. Default unit is bytes, unless specified otherwise. This prevents Spark from memory mapping very small blocks. In general, memory mapping has high overhead for blocks close to or below the page size of the operating system.""",
                                            is_required=False,
                                        ),
                                        "decommission": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        StringSource,
                                                        description="""Execution Behavior: Whether to decommission the block manager when decommissioning executor.""",
                                                        is_required=False,
                                                    ),
                                                    "shuffleBlocks": Field(
                                                        Permissive(
                                                            fields={
                                                                "enabled": Field(
                                                                    StringSource,
                                                                    description="""Execution Behavior: Whether to transfer shuffle blocks during block manager decommissioning. Requires a migratable shuffle resolver (like sort based shuffle).""",
                                                                    is_required=False,
                                                                ),
                                                                "maxThreads": Field(
                                                                    StringSource,
                                                                    description="""Execution Behavior: Maximum number of threads to use in migrating shuffle files.""",
                                                                    is_required=False,
                                                                ),
                                                                "maxDiskSize": Field(
                                                                    StringSource,
                                                                    description="""Execution Behavior: Maximum disk space to use to store shuffle blocks before rejecting remote shuffle blocks. Rejecting remote shuffle blocks means that an executor will not receive any shuffle migrations, and if there are no other executors available for migration then shuffle blocks will be lost unless spark.storage.decommission.fallbackStorage.path is configured.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                    "rddBlocks": Field(
                                                        Permissive(
                                                            fields={
                                                                "enabled": Field(
                                                                    StringSource,
                                                                    description="""Execution Behavior: Whether to transfer RDD blocks during block manager decommissioning.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                    "fallbackStorage": Field(
                                                        Permissive(
                                                            fields={
                                                                "path": Field(
                                                                    StringSource,
                                                                    description="""Execution Behavior: The location for fallback storage during block manager decommissioning. For example, s3a://spark-storage/. In case of empty, fallback storage is disabled. The storage should be managed by TTL because Spark will not clean it up.""",
                                                                    is_required=False,
                                                                ),
                                                                "cleanUp": Field(
                                                                    StringSource,
                                                                    description="""Execution Behavior: If true, Spark cleans up its fallback storage data during shutting down.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "cleaner": Field(
                                Permissive(
                                    fields={
                                        "periodicGC": Field(
                                            Permissive(
                                                fields={
                                                    "interval": Field(
                                                        StringSource,
                                                        description="""Memory Management: Controls how often to trigger a garbage collection. This context cleaner triggers cleanups only when weak references are garbage collected. In long-running applications with large driver JVMs, where there is little memory pressure on the driver, this may happen very occasionally or not at all. Not cleaning at all may lead to executors running out of disk space after a while.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "referenceTracking": Field(
                                            Permissive(
                                                fields={
                                                    "root": Field(
                                                        Bool,
                                                        description="""Memory Management: Enables or disables context cleaning.""",
                                                        is_required=False,
                                                    ),
                                                    "blocking": Field(
                                                        Permissive(
                                                            fields={
                                                                "root": Field(
                                                                    Bool,
                                                                    description="""Memory Management: Controls whether the cleaning thread should block on cleanup tasks (other than shuffle, which is controlled by spark.cleaner.referenceTracking.blocking.shuffle Spark property).""",
                                                                    is_required=False,
                                                                ),
                                                                "shuffle": Field(
                                                                    Bool,
                                                                    description="""Memory Management: Controls whether the cleaning thread should block on shuffle cleanup tasks.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                    "cleanCheckpoints": Field(
                                                        Bool,
                                                        description="""Memory Management: Controls whether to clean checkpoint files if the reference is out of scope.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "default": Field(
                                Permissive(
                                    fields={
                                        "parallelism": Field(
                                            IntSource,
                                            description="""Execution Behavior: Default number of partitions in RDDs returned by transformations like join, reduceByKey, and parallelize when not set by user.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "hadoop": Field(
                                Permissive(
                                    fields={
                                        "cloneConf": Field(
                                            Bool,
                                            description="""Execution Behavior: If set to true, clones a new Hadoop Configuration object for each task. This option should be enabled to work around Configuration thread-safety issues (see SPARK-2546 for more details). This is disabled by default in order to avoid unexpected performance regressions for jobs that are not affected by these issues.""",
                                            is_required=False,
                                        ),
                                        "validateOutputSpecs": Field(
                                            Bool,
                                            description="""Execution Behavior: If set to true, validates the output specification (e.g. checking if the output directory already exists) used in saveAsHadoopFile and other variants. This can be disabled to silence exceptions due to pre-existing output directories. We recommend that users do not disable this except if trying to achieve compatibility with previous versions of Spark. Simply use Hadoop's FileSystem API to delete output directories by hand. This setting is ignored for jobs generated through Spark Streaming's StreamingContext, since data may need to be rewritten to pre-existing output directories during checkpoint recovery.""",
                                            is_required=False,
                                        ),
                                        "mapreduce": Field(
                                            Permissive(
                                                fields={
                                                    "fileoutputcommitter": Field(
                                                        Permissive(
                                                            fields={
                                                                "algorithm": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "version": Field(
                                                                                IntSource,
                                                                                description="""Execution Behavior: The file output committer algorithm version, valid algorithm version number: 1 or 2. Note that 2 may cause a correctness issue like MAPREDUCE-7282.""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "rpc": Field(
                                Permissive(
                                    fields={
                                        "message": Field(
                                            Permissive(
                                                fields={
                                                    "maxSize": Field(
                                                        StringSource,
                                                        description="""Networking: Maximum message size (in MiB) to allow in "control plane" communication; generally only applies to map output size information sent between executors and the driver. Increase this if you are running jobs with many thousands of map and reduce tasks and see messages about the RPC message size.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "io": Field(
                                            Permissive(
                                                fields={
                                                    "backLog": Field(
                                                        StringSource,
                                                        description="""Networking: Length of the accept queue for the RPC server. For large applications, this value may need to be increased, so that incoming connections are not dropped when a large number of connections arrives in a short period of time.""",
                                                        is_required=False,
                                                    ),
                                                    "connectionTimeout": Field(
                                                        StringSource,
                                                        description="""Networking: Timeout for the established connections between RPC peers to be marked as idled and closed if there are outstanding RPC requests but no traffic on the channel for at least `connectionTimeout`.""",
                                                        is_required=False,
                                                    ),
                                                    "connectionCreationTimeout": Field(
                                                        StringSource,
                                                        description="""Networking: Timeout for establishing a connection between RPC peers.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "askTimeout": Field(
                                            StringSource,
                                            description="""Networking: Duration for an RPC ask operation to wait before timing out.""",
                                            is_required=False,
                                        ),
                                        "lookupTimeout": Field(
                                            StringSource,
                                            description="""Networking: Duration for an RPC remote endpoint lookup operation to wait before timing out.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "blockManager": Field(
                                Permissive(
                                    fields={
                                        "port": Field(
                                            StringSource,
                                            description="""Networking: Port for all block managers to listen on. These exist on both the driver and the executors.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "network": Field(
                                Permissive(
                                    fields={
                                        "timeout": Field(
                                            StringSource,
                                            description="""Networking: Default timeout for all network interactions. This config will be used in place of spark.storage.blockManagerHeartbeatTimeoutMs, spark.shuffle.io.connectionTimeout, spark.rpc.askTimeout or spark.rpc.lookupTimeout if they are not configured.""",
                                            is_required=False,
                                        ),
                                        "timeoutInterval": Field(
                                            StringSource,
                                            description="""Networking: Interval for the driver to check and expire dead executors.""",
                                            is_required=False,
                                        ),
                                        "io": Field(
                                            Permissive(
                                                fields={
                                                    "preferDirectBufs": Field(
                                                        StringSource,
                                                        description="""Networking: If enabled then off-heap buffer allocations are preferred by the shared allocators. Off-heap buffers are used to reduce garbage collection during shuffle and cache block transfer. For environments where off-heap memory is tightly limited, users may wish to turn this off to force all allocations to be on-heap.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "maxRemoteBlockSizeFetchToMem": Field(
                                            StringSource,
                                            description="""Networking: Remote block will be fetched to disk when size of the block is above this threshold in bytes. This is to avoid a giant request takes too much memory. Note this configuration will affect both shuffle fetch and block manager remote block fetch. For users who enabled external shuffle service, this feature can only work when external shuffle service is at least 2.3.0.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "port": Field(
                                Permissive(
                                    fields={
                                        "maxRetries": Field(
                                            StringSource,
                                            description="""Networking: Maximum number of retries when binding to a port before giving up. When a port is given a specific value (non 0), each subsequent retry will increment the port used in the previous attempt by 1 before retrying. This essentially allows it to try a range of ports from the start port specified to port + maxRetries.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "cores": Field(
                                Permissive(
                                    fields={
                                        "max": Field(
                                            StringSource,
                                            description="""Scheduling: When running on a standalone deploy cluster or a Mesos cluster in "coarse-grained" sharing mode, the maximum amount of CPU cores to request for the application from across the cluster (not from each machine). If not set, the default will be spark.deploy.defaultCores on Spark's standalone cluster manager, or infinite (all available cores) on Mesos.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "locality": Field(
                                Permissive(
                                    fields={
                                        "wait": Field(
                                            Permissive(
                                                fields={
                                                    "root": Field(
                                                        StringSource,
                                                        description="""Scheduling: How long to wait to launch a data-local task before giving up and launching it on a less-local node. The same wait will be used to step through multiple locality levels (process-local, node-local, rack-local and then any). It is also possible to customize the waiting time for each level by setting spark.locality.wait.node, etc. You should increase this setting if your tasks are long and see poor locality, but the default usually works well.""",
                                                        is_required=False,
                                                    ),
                                                    "node": Field(
                                                        StringSource,
                                                        description="""Scheduling: Customize the locality wait for node locality. For example, you can set this to 0 to skip node locality and search immediately for rack locality (if your cluster has rack information).""",
                                                        is_required=False,
                                                    ),
                                                    "process": Field(
                                                        StringSource,
                                                        description="""Scheduling: Customize the locality wait for process locality. This affects tasks that attempt to access cached data in a particular executor process.""",
                                                        is_required=False,
                                                    ),
                                                    "rack": Field(
                                                        StringSource,
                                                        description="""Scheduling: Customize the locality wait for rack locality.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "scheduler": Field(
                                Permissive(
                                    fields={
                                        "maxRegisteredResourcesWaitingTime": Field(
                                            StringSource,
                                            description="""Scheduling: Maximum amount of time to wait for resources to register before scheduling begins.""",
                                            is_required=False,
                                        ),
                                        "minRegisteredResourcesRatio": Field(
                                            StringSource,
                                            description="""Scheduling: The minimum ratio of registered resources (registered resources / total expected resources) (resources are executors in yarn mode and Kubernetes mode, CPU cores in standalone mode and Mesos coarse-grained mode ['spark.cores.max' value is total expected resources for Mesos coarse-grained mode] ) to wait for before scheduling begins. Specified as a double between 0.0 and 1.0. Regardless of whether the minimum ratio of resources has been reached, the maximum amount of time it will wait before scheduling begins is controlled by config spark.scheduler.maxRegisteredResourcesWaitingTime.""",
                                            is_required=False,
                                        ),
                                        "mode": Field(
                                            StringSource,
                                            description="""Scheduling: The scheduling mode between jobs submitted to the same SparkContext. Can be set to FAIR to use fair sharing instead of queueing jobs one after another. Useful for multi-user services.""",
                                            is_required=False,
                                        ),
                                        "revive": Field(
                                            Permissive(
                                                fields={
                                                    "interval": Field(
                                                        StringSource,
                                                        description="""Scheduling: The interval length for the scheduler to revive the worker resource offers to run tasks.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "listenerbus": Field(
                                            Permissive(
                                                fields={
                                                    "eventqueue": Field(
                                                        Permissive(
                                                            fields={
                                                                "capacity": Field(
                                                                    StringSource,
                                                                    description="""Scheduling: The default capacity for event queues. Spark will try to initialize an event queue using capacity specified by `spark.scheduler.listenerbus.eventqueue.queueName.capacity` first. If it's not configured, Spark will use the default capacity specified by this config. Note that capacity must be greater than 0. Consider increasing value (e.g. 20000) if listener events are dropped. Increasing this value may result in the driver using more memory.""",
                                                                    is_required=False,
                                                                ),
                                                                "shared": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "capacity": Field(
                                                                                StringSource,
                                                                                description="""Scheduling: Capacity for shared event queue in Spark listener bus, which hold events for external listener(s) that register to the listener bus. Consider increasing value, if the listener events corresponding to shared queue are dropped. Increasing this value may result in the driver using more memory.""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                                "appStatus": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "capacity": Field(
                                                                                StringSource,
                                                                                description="""Scheduling: Capacity for appStatus event queue, which hold events for internal application status listeners. Consider increasing value, if the listener events corresponding to appStatus queue are dropped. Increasing this value may result in the driver using more memory.""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                                "executorManagement": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "capacity": Field(
                                                                                StringSource,
                                                                                description="""Scheduling: Capacity for executorManagement event queue in Spark listener bus, which hold events for internal executor management listeners. Consider increasing value if the listener events corresponding to executorManagement queue are dropped. Increasing this value may result in the driver using more memory.""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                                "eventLog": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "capacity": Field(
                                                                                StringSource,
                                                                                description="""Scheduling: Capacity for eventLog queue in Spark listener bus, which hold events for Event logging listeners that write events to eventLogs. Consider increasing value if the listener events corresponding to eventLog queue are dropped. Increasing this value may result in the driver using more memory.""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                                "streams": Field(
                                                                    Permissive(
                                                                        fields={
                                                                            "capacity": Field(
                                                                                StringSource,
                                                                                description="""Scheduling: Capacity for streams queue in Spark listener bus, which hold events for internal streaming listener. Consider increasing value if the listener events corresponding to streams queue are dropped. Increasing this value may result in the driver using more memory.""",
                                                                                is_required=False,
                                                                            ),
                                                                        }
                                                                    )
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        "resource": Field(
                                            Permissive(
                                                fields={
                                                    "profileMergeConflicts": Field(
                                                        StringSource,
                                                        description="""Scheduling: If set to "true", Spark will merge ResourceProfiles when different profiles are specified in RDDs that get combined into a single stage. When they are merged, Spark chooses the maximum of each resource and creates a new ResourceProfile. The default of false results in Spark throwing an exception if multiple different ResourceProfiles are found in RDDs going into the same stage.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "excludeOnFailure": Field(
                                            Permissive(
                                                fields={
                                                    "unschedulableTaskSetTimeout": Field(
                                                        StringSource,
                                                        description="""Scheduling: The timeout in seconds to wait to acquire a new executor and schedule a task before aborting a TaskSet which is unschedulable because all executors are excluded due to task failures.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "barrier": Field(
                                            Permissive(
                                                fields={
                                                    "maxConcurrentTasksCheck": Field(
                                                        Permissive(
                                                            fields={
                                                                "interval": Field(
                                                                    StringSource,
                                                                    description="""Barrier Execution Mode: Time in seconds to wait between a max concurrent tasks check failure and the next check. A max concurrent tasks check ensures the cluster can launch more concurrent tasks than required by a barrier stage on job submitted. The check can fail in case a cluster has just started and not enough executors have registered, so we wait for a little while and try to perform the check again. If the check fails more than a configured max failure times for a job then fail current job submission. Note this config only applies to jobs that contain one or more barrier stages, we won't perform the check on non-barrier jobs.""",
                                                                    is_required=False,
                                                                ),
                                                                "maxFailures": Field(
                                                                    StringSource,
                                                                    description="""Barrier Execution Mode: Number of max concurrent tasks check failures allowed before fail a job submission. A max concurrent tasks check ensures the cluster can launch more concurrent tasks than required by a barrier stage on job submitted. The check can fail in case a cluster has just started and not enough executors have registered, so we wait for a little while and try to perform the check again. If the check fails more than a configured max failure times for a job then fail current job submission. Note this config only applies to jobs that contain one or more barrier stages, we won't perform the check on non-barrier jobs.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "standalone": Field(
                                Permissive(
                                    fields={
                                        "submit": Field(
                                            Permissive(
                                                fields={
                                                    "waitAppCompletion": Field(
                                                        StringSource,
                                                        description="""Scheduling: If set to true, Spark will merge ResourceProfiles when different profiles are specified in RDDs that get combined into a single stage. When they are merged, Spark chooses the maximum of each resource and creates a new ResourceProfile. The default of false results in Spark throwing an exception if multiple different ResourceProfiles are found in RDDs going into the same stage.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "excludeOnFailure": Field(
                                Permissive(
                                    fields={
                                        "enabled": Field(
                                            StringSource,
                                            description="""Scheduling: If set to "true", prevent Spark from scheduling tasks on executors that have been excluded due to too many task failures. The algorithm used to exclude executors and nodes can be further controlled by the other "spark.excludeOnFailure" configuration options.""",
                                            is_required=False,
                                        ),
                                        "timeout": Field(
                                            StringSource,
                                            description="""Scheduling: (Experimental) How long a node or executor is excluded for the entire application, before it is unconditionally removed from the excludelist to attempt running new tasks.""",
                                            is_required=False,
                                        ),
                                        "task": Field(
                                            Permissive(
                                                fields={
                                                    "maxTaskAttemptsPerExecutor": Field(
                                                        StringSource,
                                                        description="""Scheduling: (Experimental) For a given task, how many times it can be retried on one executor before the executor is excluded for that task.""",
                                                        is_required=False,
                                                    ),
                                                    "maxTaskAttemptsPerNode": Field(
                                                        StringSource,
                                                        description="""Scheduling: (Experimental) For a given task, how many times it can be retried on one node, before the entire node is excluded for that task.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "stage": Field(
                                            Permissive(
                                                fields={
                                                    "maxFailedTasksPerExecutor": Field(
                                                        StringSource,
                                                        description="""Scheduling: (Experimental) How many different tasks must fail on one executor, within one stage, before the executor is excluded for that stage.""",
                                                        is_required=False,
                                                    ),
                                                    "maxFailedExecutorsPerNode": Field(
                                                        StringSource,
                                                        description="""Scheduling: (Experimental) How many different executors are marked as excluded for a given stage, before the entire node is marked as failed for the stage.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "application": Field(
                                            Permissive(
                                                fields={
                                                    "maxFailedTasksPerExecutor": Field(
                                                        StringSource,
                                                        description="""Scheduling: (Experimental) How many different tasks must fail on one executor, in successful task sets, before the executor is excluded for the entire application. Excluded executors will be automatically added back to the pool of available resources after the timeout specified by spark.excludeOnFailure.timeout. Note that with dynamic allocation, though, the executors may get marked as idle and be reclaimed by the cluster manager.""",
                                                        is_required=False,
                                                    ),
                                                    "maxFailedExecutorsPerNode": Field(
                                                        StringSource,
                                                        description="""Scheduling: (Experimental) How many different executors must be excluded for the entire application, before the node is excluded for the entire application. Excluded nodes will be automatically added back to the pool of available resources after the timeout specified by spark.excludeOnFailure.timeout. Note that with dynamic allocation, though, the executors on the node may get marked as idle and be reclaimed by the cluster manager.""",
                                                        is_required=False,
                                                    ),
                                                    "fetchFailure": Field(
                                                        Permissive(
                                                            fields={
                                                                "enabled": Field(
                                                                    StringSource,
                                                                    description="""Scheduling: (Experimental) If set to "true", Spark will exclude the executor immediately when a fetch failure happens. If external shuffle service is enabled, then the whole node will be excluded.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        "killExcludedExecutors": Field(
                                            StringSource,
                                            description="""Scheduling: (Experimental) If set to "true", allow Spark to automatically kill the executors when they are excluded on fetch failure or excluded for the entire application, as controlled by spark.killExcludedExecutors.application.*. Note that, when an entire node is added excluded, all of the executors on that node will be killed.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "speculation": Field(
                                Permissive(
                                    fields={
                                        "root": Field(
                                            StringSource,
                                            description="""Scheduling: If set to "true", performs speculative execution of tasks. This means if one or more tasks are running slowly in a stage, they will be re-launched.""",
                                            is_required=False,
                                        ),
                                        "interval": Field(
                                            StringSource,
                                            description="""Scheduling: How often Spark will check for tasks to speculate.""",
                                            is_required=False,
                                        ),
                                        "multiplier": Field(
                                            StringSource,
                                            description="""Scheduling: How many times slower a task is than the median to be considered for speculation.""",
                                            is_required=False,
                                        ),
                                        "quantile": Field(
                                            StringSource,
                                            description="""Scheduling: Fraction of tasks which must be complete before speculation is enabled for a particular stage.""",
                                            is_required=False,
                                        ),
                                        "minTaskRuntime": Field(
                                            StringSource,
                                            description="""Scheduling: Minimum amount of time a task runs before being considered for speculation. This can be used to avoid launching speculative copies of tasks that are very short.""",
                                            is_required=False,
                                        ),
                                        "task": Field(
                                            Permissive(
                                                fields={
                                                    "duration": Field(
                                                        Permissive(
                                                            fields={
                                                                "threshold": Field(
                                                                    StringSource,
                                                                    description="""Scheduling: Task duration after which scheduler would try to speculative run the task. If provided, tasks would be speculatively run if current stage contains less tasks than or equal to the number of slots on a single executor and the task is taking longer time than the threshold. This config helps speculate stage with very few tasks. Regular speculation configs may also apply if the executor slots are large enough. E.g. tasks might be re-launched if there are enough successful runs even though the threshold hasn't been reached. The number of slots is computed based on the conf values of spark.executor.cores and spark.task.cpus minimum 1. Default unit is bytes, unless otherwise specified.""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        "efficiency": Field(
                                            Permissive(
                                                fields={
                                                    "processRateMultiplier": Field(
                                                        StringSource,
                                                        description="""Scheduling: A multiplier that used when evaluating inefficient tasks. The higher the multiplier is, the more tasks will be possibly considered as inefficient.""",
                                                        is_required=False,
                                                    ),
                                                    "longRunTaskFactor": Field(
                                                        StringSource,
                                                        description="""Scheduling: A task will be speculated anyway as long as its duration has exceeded the value of multiplying the factor and the time threshold (either be spark.speculation.multiplier * successfulTaskDurations.median or spark.speculation.minTaskRuntime) regardless of it's data process rate is good or not. This avoids missing the inefficient tasks when task slow isn't related to data process rate.""",
                                                        is_required=False,
                                                    ),
                                                    "enabled": Field(
                                                        StringSource,
                                                        description="""Scheduling: When set to true, spark will evaluate the efficiency of task processing through the stage task metrics or its duration, and only need to speculate the inefficient tasks. A task is inefficient when 1)its data process rate is less than the average data process rate of all successful tasks in the stage multiplied by a multiplier or 2)its duration has exceeded the value of multiplying spark.speculation.efficiency.longRunTaskFactor and the time threshold (either be spark.speculation.multiplier * successfulTaskDurations.median or spark.speculation.minTaskRuntime).""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "task": Field(
                                Permissive(
                                    fields={
                                        "cpus": Field(
                                            StringSource,
                                            description="""Scheduling: Number of cores to allocate for each task.""",
                                            is_required=False,
                                        ),
                                        "resource": Field(
                                            Permissive(
                                                fields={
                                                    "{resourceName}": Field(
                                                        Permissive(
                                                            fields={
                                                                "amount": Field(
                                                                    StringSource,
                                                                    description="""Scheduling: Amount of a particular resource type to allocate for each task, note that this can be a double. If this is specified you must also provide the executor config spark.executor.resource.{resourceName}.amount and any corresponding discovery configs so that your executors are created with that resource type. In addition to whole amounts, a fractional amount (for example, 0.25, which means 1/4th of a resource) may be specified. Fractional amounts must be less than or equal to 0.5, or in other words, the minimum amount of resource sharing is 2 tasks per resource. Additionally, fractional amounts are floored in order to assign resource slots (e.g. a 0.2222 configuration, or 1/0.2222 slots will become 4 tasks/resource, not 5).""",
                                                                    is_required=False,
                                                                ),
                                                            }
                                                        )
                                                    ),
                                                }
                                            )
                                        ),
                                        "maxFailures": Field(
                                            StringSource,
                                            description="""Scheduling: Number of continuous failures of any particular task before giving up on the job. The total number of failures spread across different tasks will not cause the job to fail; a particular task has to fail this number of attempts continuously. If any attempt succeeds, the failure count for the task will be reset. Should be greater than or equal to 1. Number of allowed retries = this value - 1.""",
                                            is_required=False,
                                        ),
                                        "reaper": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        StringSource,
                                                        description="""Scheduling: Enables monitoring of killed / interrupted tasks. When set to true, any task which is killed will be monitored by the executor until that task actually finishes executing. See the other spark.task.reaper.* configurations for details on how to control the exact behavior of this monitoring. When set to false (the default), task killing will use an older code path which lacks such monitoring.""",
                                                        is_required=False,
                                                    ),
                                                    "pollingInterval": Field(
                                                        StringSource,
                                                        description="""Scheduling: When spark.task.reaper.enabled = true, this setting controls the frequency at which executors will poll the status of killed tasks. If a killed task is still running when polled then a warning will be logged and, by default, a thread-dump of the task will be logged (this thread dump can be disabled via the spark.task.reaper.threadDump setting, which is documented below).""",
                                                        is_required=False,
                                                    ),
                                                    "threadDump": Field(
                                                        StringSource,
                                                        description="""Scheduling: When spark.task.reaper.enabled = true, this setting controls whether task thread dumps are logged during periodic polling of killed tasks. Set this to false to disable collection of thread dumps.""",
                                                        is_required=False,
                                                    ),
                                                    "killTimeout": Field(
                                                        StringSource,
                                                        description="""Scheduling: When spark.task.reaper.enabled = true, this setting specifies a timeout after which the executor JVM will kill itself if a killed task has not stopped running. The default value, -1, disables this mechanism and prevents the executor from self-destructing. The purpose of this setting is to act as a safety-net to prevent runaway noncancellable tasks from rendering an executor unusable.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "stage": Field(
                                Permissive(
                                    fields={
                                        "maxConsecutiveAttempts": Field(
                                            StringSource,
                                            description="""Scheduling: Number of consecutive stage attempts allowed before a stage is aborted.""",
                                            is_required=False,
                                        ),
                                        "ignoreDecommissionFetchFailure": Field(
                                            StringSource,
                                            description="""Scheduling: Whether ignore stage fetch failure caused by executor decommission when count spark.stage.maxConsecutiveAttempts""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "barrier": Field(
                                Permissive(
                                    fields={
                                        "sync": Field(
                                            Permissive(
                                                fields={
                                                    "timeout": Field(
                                                        StringSource,
                                                        description="""Barrier Execution Mode: The timeout in seconds for each barrier() call from a barrier task. If the coordinator didn't receive all the sync messages from barrier tasks within the configured time, throw a SparkException to fail all the tasks. The default value is set to 31536000(3600 * 24 * 365) so the barrier() call shall wait for one year.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "dynamicAllocation": Field(
                                Permissive(
                                    fields={
                                        "enabled": Field(
                                            StringSource,
                                            description="""Dynamic Allocation: Whether to use dynamic resource allocation, which scales the number of executors registered with this application up and down based on the workload. For more detail, see the description here. This requires one of the following conditions: 1) enabling external shuffle service through spark.shuffle.service.enabled, or 2) enabling shuffle tracking through spark.dynamicAllocation.shuffleTracking.enabled, or 3) enabling shuffle blocks decommission through spark.decommission.enabled and spark.storage.decommission.shuffleBlocks.enabled, or 4) (Experimental) configuring spark.shuffle.sort.io.plugin.class to use a custom ShuffleDataIO who's ShuffleDriverComponents supports reliable storage. The following configurations are also relevant: spark.dynamicAllocation.minExecutors, spark.dynamicAllocation.maxExecutors, and spark.dynamicAllocation.initialExecutors spark.dynamicAllocation.executorAllocationRatio""",
                                            is_required=False,
                                        ),
                                        "executorIdleTimeout": Field(
                                            StringSource,
                                            description="""Dynamic Allocation: If dynamic allocation is enabled and an executor has been idle for more than this duration, the executor will be removed. For more detail, see this description.""",
                                            is_required=False,
                                        ),
                                        "cachedExecutorIdleTimeout": Field(
                                            StringSource,
                                            description="""Dynamic Allocation: If dynamic allocation is enabled and an executor which has cached data blocks has been idle for more than this duration, the executor will be removed. For more details, see this description.""",
                                            is_required=False,
                                        ),
                                        "initialExecutors": Field(
                                            StringSource,
                                            description="""Dynamic Allocation: Initial number of executors to run if dynamic allocation is enabled. If `--num-executors` (or `spark.executor.instances`) is set and larger than this value, it will be used as the initial number of executors.""",
                                            is_required=False,
                                        ),
                                        "maxExecutors": Field(
                                            StringSource,
                                            description="""Dynamic Allocation: Upper bound for the number of executors if dynamic allocation is enabled.""",
                                            is_required=False,
                                        ),
                                        "minExecutors": Field(
                                            StringSource,
                                            description="""Dynamic Allocation: Lower bound for the number of executors if dynamic allocation is enabled.""",
                                            is_required=False,
                                        ),
                                        "executorAllocationRatio": Field(
                                            StringSource,
                                            description="""Dynamic Allocation: By default, the dynamic allocation will request enough executors to maximize the parallelism according to the number of tasks to process. While this minimizes the latency of the job, with small tasks this setting can waste a lot of resources due to executor allocation overhead, as some executor might not even do any work. This setting allows to set a ratio that will be used to reduce the number of executors w.r.t. full parallelism. Defaults to 1.0 to give maximum parallelism. 0.5 will divide the target number of executors by 2 The target number of executors computed by the dynamicAllocation can still be overridden by the spark.dynamicAllocation.minExecutors and spark.dynamicAllocation.maxExecutors settings""",
                                            is_required=False,
                                        ),
                                        "schedulerBacklogTimeout": Field(
                                            StringSource,
                                            description="""Dynamic Allocation: If dynamic allocation is enabled and there have been pending tasks backlogged for more than this duration, new executors will be requested. For more detail, see this description.""",
                                            is_required=False,
                                        ),
                                        "sustainedSchedulerBacklogTimeout": Field(
                                            StringSource,
                                            description="""Dynamic Allocation: Same as spark.dynamicAllocation.schedulerBacklogTimeout, but used only for subsequent executor requests. For more detail, see this description.""",
                                            is_required=False,
                                        ),
                                        "shuffleTracking": Field(
                                            Permissive(
                                                fields={
                                                    "enabled": Field(
                                                        StringSource,
                                                        description="""Dynamic Allocation: Enables shuffle file tracking for executors, which allows dynamic allocation without the need for an external shuffle service. This option will try to keep alive executors that are storing shuffle data for active jobs.""",
                                                        is_required=False,
                                                    ),
                                                    "timeout": Field(
                                                        StringSource,
                                                        description="""Dynamic Allocation: When shuffle tracking is enabled, controls the timeout for executors that are holding shuffle data. The default value means that Spark will rely on the shuffles being garbage collected to be able to release executors. If for some reason garbage collection is not cleaning up shuffles quickly enough, this option can be used to control when to time out executors even when they are storing shuffle data.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "r": Field(
                                Permissive(
                                    fields={
                                        "numRBackendThreads": Field(
                                            StringSource,
                                            description="""SparkR: Number of threads used by RBackend to handle RPC calls from SparkR package.""",
                                            is_required=False,
                                        ),
                                        "command": Field(
                                            StringSource,
                                            description="""SparkR: Executable for executing R scripts in cluster modes for both driver and workers.""",
                                            is_required=False,
                                        ),
                                        "driver": Field(
                                            Permissive(
                                                fields={
                                                    "command": Field(
                                                        StringSource,
                                                        description="""SparkR: Executable for executing R scripts in client modes for driver. Ignored in cluster modes.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "shell": Field(
                                            Permissive(
                                                fields={
                                                    "command": Field(
                                                        StringSource,
                                                        description="""SparkR: Executable for executing sparkR shell in client modes for driver. Ignored in cluster modes. It is the same as environment variable SPARKR_DRIVER_R, but take precedence over it. spark.r.shell.command is used for sparkR shell while spark.r.driver.command is used for running R script.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                        "backendConnectionTimeout": Field(
                                            StringSource,
                                            description="""SparkR: Connection timeout set by R process on its connection to RBackend in seconds.""",
                                            is_required=False,
                                        ),
                                        "heartBeatInterval": Field(
                                            StringSource,
                                            description="""SparkR: Interval for heartbeats sent from SparkR backend to R process to prevent connection timeout.""",
                                            is_required=False,
                                        ),
                                    }
                                )
                            ),
                            "graphx": Field(
                                Permissive(
                                    fields={
                                        "pregel": Field(
                                            Permissive(
                                                fields={
                                                    "checkpointInterval": Field(
                                                        StringSource,
                                                        description="""GraphX: Checkpoint interval for graph and message in Pregel. It used to avoid stackOverflowError due to long lineage chains after lots of iterations. The checkpoint is disabled by default.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                            "deploy": Field(
                                Permissive(
                                    fields={
                                        "recoveryMode": Field(
                                            StringSource,
                                            description="""Deploy: The recovery mode setting to recover submitted Spark jobs with cluster mode when it failed and relaunches. This is only applicable for cluster mode when running with Standalone or Mesos.""",
                                            is_required=False,
                                        ),
                                        "zookeeper": Field(
                                            Permissive(
                                                fields={
                                                    "url": Field(
                                                        StringSource,
                                                        description="""Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper URL to connect to.""",
                                                        is_required=False,
                                                    ),
                                                    "dir": Field(
                                                        StringSource,
                                                        description="""Deploy: When `spark.deploy.recoveryMode` is set to ZOOKEEPER, this configuration is used to set the zookeeper directory to store recovery state.""",
                                                        is_required=False,
                                                    ),
                                                }
                                            )
                                        ),
                                    }
                                )
                            ),
                        }
                    )
                ),
            }
        )
    )
