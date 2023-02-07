"""NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT.

@generated

Produced via:
parse_dataproc_configs.py \

"""


from dagster import Bool, Field, Int, Permissive, Shape, String


def define_dataproc_job_config():
    return Field(
        Shape(
            fields={
                "status": Field(
                    Shape(fields={}),
                    description="""Cloud Dataproc job status.""",
                    is_required=False,
                ),
                "placement": Field(
                    Shape(
                        fields={
                            "clusterName": Field(
                                String,
                                description="""Required. The name of the cluster where the job will
                                be submitted.""",
                                is_required=False,
                            )
                        }
                    ),
                    description="""Cloud Dataproc job config.""",
                    is_required=False,
                ),
                "scheduling": Field(
                    Shape(
                        fields={
                            "maxFailuresPerHour": Field(
                                Int,
                                description="""Optional. Maximum number of times per hour a driver
                                may be restarted as a result of driver terminating with non-zero
                                code before job is reported failed.A job may be reported as
                                thrashing if driver exits with non-zero code 4 times within 10
                                minute window.Maximum value is 10.""",
                                is_required=False,
                            )
                        }
                    ),
                    description="""Job scheduling options.""",
                    is_required=False,
                ),
                "pigJob": Field(
                    Shape(
                        fields={
                            "queryFileUri": Field(
                                String,
                                description="""The HCFS URI of the script that contains the Pig
                                queries.""",
                                is_required=False,
                            ),
                            "queryList": Field(
                                Shape(
                                    fields={
                                        "queries": Field(
                                            [String],
                                            description="""Required. The queries to execute. You do
                                            not need to terminate a query with a semicolon. Multiple
                                            queries can be specified in one string by separating
                                            each with a semicolon. Here is an example of an Cloud
                                            Dataproc API snippet that uses a QueryList to specify a
                                            HiveJob: "hiveJob": {   "queryList": {     "queries": [
                                            "query1",       "query2",       "query3;query4",     ]
                                            } } """,
                                            is_required=False,
                                        )
                                    }
                                ),
                                description="""A list of queries to run on a cluster.""",
                                is_required=False,
                            ),
                            "jarFileUris": Field(
                                [String],
                                description="""Optional. HCFS URIs of jar files to add to the
                                CLASSPATH of the Pig Client and Hadoop MapReduce (MR) tasks. Can
                                contain Pig UDFs.""",
                                is_required=False,
                            ),
                            "scriptVariables": Field(
                                Permissive(),
                                description="""Optional. Mapping of query variable names to values
                                (equivalent to the Pig command: name=[value]).""",
                                is_required=False,
                            ),
                            "loggingConfig": Field(
                                Shape(
                                    fields={
                                        "driverLogLevels": Field(
                                            Permissive(),
                                            description="""The per-package log levels for the
                                            driver. This may include "root" package name to
                                            configure rootLogger. Examples:  \'com.google = FATAL\',
                                            \'root = INFO\', \'org.apache = DEBUG\'""",
                                            is_required=False,
                                        )
                                    }
                                ),
                                description="""The runtime logging config of the job.""",
                                is_required=False,
                            ),
                            "properties": Field(
                                Permissive(),
                                description="""Optional. A mapping of property names to values, used
                                to configure Pig. Properties that conflict with values set by the
                                Cloud Dataproc API may be overwritten. Can include properties set in
                                /etc/hadoop/conf/*-site.xml, /etc/pig/conf/pig.properties, and
                                classes in user code.""",
                                is_required=False,
                            ),
                            "continueOnFailure": Field(
                                Bool,
                                description="""Optional. Whether to continue executing queries if a
                                query fails. The default value is false. Setting to true can be
                                useful when executing independent parallel queries.""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""A Cloud Dataproc job for running Apache Pig
                    (https://pig.apache.org/) queries on YARN.""",
                    is_required=False,
                ),
                "hiveJob": Field(
                    Shape(
                        fields={
                            "continueOnFailure": Field(
                                Bool,
                                description="""Optional. Whether to continue executing queries if a
                                query fails. The default value is false. Setting to true can be
                                useful when executing independent parallel queries.""",
                                is_required=False,
                            ),
                            "queryFileUri": Field(
                                String,
                                description="""The HCFS URI of the script that contains Hive
                                queries.""",
                                is_required=False,
                            ),
                            "queryList": Field(
                                Shape(
                                    fields={
                                        "queries": Field(
                                            [String],
                                            description="""Required. The queries to execute. You do
                                            not need to terminate a query with a semicolon. Multiple
                                            queries can be specified in one string by separating
                                            each with a semicolon. Here is an example of an Cloud
                                            Dataproc API snippet that uses a QueryList to specify a
                                            HiveJob: "hiveJob": {   "queryList": {     "queries": [
                                            "query1",       "query2",       "query3;query4",     ]
                                            } } """,
                                            is_required=False,
                                        )
                                    }
                                ),
                                description="""A list of queries to run on a cluster.""",
                                is_required=False,
                            ),
                            "jarFileUris": Field(
                                [String],
                                description="""Optional. HCFS URIs of jar files to add to the
                                CLASSPATH of the Hive server and Hadoop MapReduce (MR) tasks. Can
                                contain Hive SerDes and UDFs.""",
                                is_required=False,
                            ),
                            "scriptVariables": Field(
                                Permissive(),
                                description="""Optional. Mapping of query variable names to values
                                (equivalent to the Hive command: SET name="value";).""",
                                is_required=False,
                            ),
                            "properties": Field(
                                Permissive(),
                                description="""Optional. A mapping of property names and values,
                                used to configure Hive. Properties that conflict with values set by
                                the Cloud Dataproc API may be overwritten. Can include properties
                                set in /etc/hadoop/conf/*-site.xml, /etc/hive/conf/hive-site.xml,
                                and classes in user code.""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""A Cloud Dataproc job for running Apache Hive
                    (https://hive.apache.org/) queries on YARN.""",
                    is_required=False,
                ),
                "labels": Field(
                    Permissive(),
                    description="""Optional. The labels to associate with this job. Label keys must
                    contain 1 to 63 characters, and must conform to RFC 1035
                    (https://www.ietf.org/rfc/rfc1035.txt). Label values may be empty, but, if
                    present, must contain 1 to 63 characters, and must conform to RFC 1035
                    (https://www.ietf.org/rfc/rfc1035.txt). No more than 32 labels can be associated
                    with a job.""",
                    is_required=False,
                ),
                "sparkJob": Field(
                    Shape(
                        fields={
                            "archiveUris": Field(
                                [String],
                                description="""Optional. HCFS URIs of archives to be extracted in
                                the working directory of Spark drivers and tasks. Supported file
                                types: .jar, .tar, .tar.gz, .tgz, and .zip.""",
                                is_required=False,
                            ),
                            "mainJarFileUri": Field(
                                String,
                                description="""The HCFS URI of the jar file that contains the main
                                class.""",
                                is_required=False,
                            ),
                            "jarFileUris": Field(
                                [String],
                                description="""Optional. HCFS URIs of jar files to add to the
                                CLASSPATHs of the Spark driver and tasks.""",
                                is_required=False,
                            ),
                            "loggingConfig": Field(
                                Shape(
                                    fields={
                                        "driverLogLevels": Field(
                                            Permissive(),
                                            description="""The per-package log levels for the
                                            driver. This may include "root" package name to
                                            configure rootLogger. Examples:  \'com.google = FATAL\',
                                            \'root = INFO\', \'org.apache = DEBUG\'""",
                                            is_required=False,
                                        )
                                    }
                                ),
                                description="""The runtime logging config of the job.""",
                                is_required=False,
                            ),
                            "properties": Field(
                                Permissive(),
                                description="""Optional. A mapping of property names to values, used
                                to configure Spark. Properties that conflict with values set by the
                                Cloud Dataproc API may be overwritten. Can include properties set in
                                /etc/spark/conf/spark-defaults.conf and classes in user code.""",
                                is_required=False,
                            ),
                            "args": Field(
                                [String],
                                description="""Optional. The arguments to pass to the driver. Do not
                                include arguments, such as --conf, that can be set as job
                                properties, since a collision may occur that causes an incorrect job
                                submission.""",
                                is_required=False,
                            ),
                            "fileUris": Field(
                                [String],
                                description="""Optional. HCFS URIs of files to be copied to the
                                working directory of Spark drivers and distributed tasks. Useful for
                                naively parallel tasks.""",
                                is_required=False,
                            ),
                            "mainClass": Field(
                                String,
                                description="""The name of the driver\'s main class. The jar file
                                that contains the class must be in the default CLASSPATH or
                                specified in jar_file_uris.""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""A Cloud Dataproc job for running Apache Spark
                    (http://spark.apache.org/) applications on YARN.""",
                    is_required=False,
                ),
                "sparkSqlJob": Field(
                    Shape(
                        fields={
                            "queryList": Field(
                                Shape(
                                    fields={
                                        "queries": Field(
                                            [String],
                                            description="""Required. The queries to execute. You do
                                            not need to terminate a query with a semicolon. Multiple
                                            queries can be specified in one string by separating
                                            each with a semicolon. Here is an example of an Cloud
                                            Dataproc API snippet that uses a QueryList to specify a
                                            HiveJob: "hiveJob": {   "queryList": {     "queries": [
                                            "query1",       "query2",       "query3;query4",     ]
                                            } } """,
                                            is_required=False,
                                        )
                                    }
                                ),
                                description="""A list of queries to run on a cluster.""",
                                is_required=False,
                            ),
                            "queryFileUri": Field(
                                String,
                                description="""The HCFS URI of the script that contains SQL
                                queries.""",
                                is_required=False,
                            ),
                            "scriptVariables": Field(
                                Permissive(),
                                description="""Optional. Mapping of query variable names to values
                                (equivalent to the Spark SQL command: SET name="value";).""",
                                is_required=False,
                            ),
                            "jarFileUris": Field(
                                [String],
                                description="""Optional. HCFS URIs of jar files to be added to the
                                Spark CLASSPATH.""",
                                is_required=False,
                            ),
                            "loggingConfig": Field(
                                Shape(
                                    fields={
                                        "driverLogLevels": Field(
                                            Permissive(),
                                            description="""The per-package log levels for the
                                            driver. This may include "root" package name to
                                            configure rootLogger. Examples:  \'com.google = FATAL\',
                                            \'root = INFO\', \'org.apache = DEBUG\'""",
                                            is_required=False,
                                        )
                                    }
                                ),
                                description="""The runtime logging config of the job.""",
                                is_required=False,
                            ),
                            "properties": Field(
                                Permissive(),
                                description="""Optional. A mapping of property names to values, used
                                to configure Spark SQL\'s SparkConf. Properties that conflict with
                                values set by the Cloud Dataproc API may be overwritten.""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""A Cloud Dataproc job for running Apache Spark SQL
                    (http://spark.apache.org/sql/) queries.""",
                    is_required=False,
                ),
                "pysparkJob": Field(
                    Shape(
                        fields={
                            "jarFileUris": Field(
                                [String],
                                description="""Optional. HCFS URIs of jar files to add to the
                                CLASSPATHs of the Python driver and tasks.""",
                                is_required=False,
                            ),
                            "loggingConfig": Field(
                                Shape(
                                    fields={
                                        "driverLogLevels": Field(
                                            Permissive(),
                                            description="""The per-package log levels for the
                                            driver. This may include "root" package name to
                                            configure rootLogger. Examples:  \'com.google = FATAL\',
                                            \'root = INFO\', \'org.apache = DEBUG\'""",
                                            is_required=False,
                                        )
                                    }
                                ),
                                description="""The runtime logging config of the job.""",
                                is_required=False,
                            ),
                            "properties": Field(
                                Permissive(),
                                description="""Optional. A mapping of property names to values, used
                                to configure PySpark. Properties that conflict with values set by
                                the Cloud Dataproc API may be overwritten. Can include properties
                                set in /etc/spark/conf/spark-defaults.conf and classes in user
                                code.""",
                                is_required=False,
                            ),
                            "args": Field(
                                [String],
                                description="""Optional. The arguments to pass to the driver. Do not
                                include arguments, such as --conf, that can be set as job
                                properties, since a collision may occur that causes an incorrect job
                                submission.""",
                                is_required=False,
                            ),
                            "fileUris": Field(
                                [String],
                                description="""Optional. HCFS URIs of files to be copied to the
                                working directory of Python drivers and distributed tasks. Useful
                                for naively parallel tasks.""",
                                is_required=False,
                            ),
                            "pythonFileUris": Field(
                                [String],
                                description="""Optional. HCFS file URIs of Python files to pass to
                                the PySpark framework. Supported file types: .py, .egg, and
                                .zip.""",
                                is_required=False,
                            ),
                            "mainPythonFileUri": Field(
                                String,
                                description="""Required. The HCFS URI of the main Python file to use
                                as the driver. Must be a .py file.""",
                                is_required=False,
                            ),
                            "archiveUris": Field(
                                [String],
                                description="""Optional. HCFS URIs of archives to be extracted in
                                the working directory of .jar, .tar, .tar.gz, .tgz, and .zip.""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""A Cloud Dataproc job for running Apache PySpark
                    (https://spark.apache.org/docs/0.9.0/python-programming-guide.html) applications
                    on YARN.""",
                    is_required=False,
                ),
                "reference": Field(
                    Shape(
                        fields={
                            "projectId": Field(
                                String,
                                description="""Required. The ID of the Google Cloud Platform project
                                that the job belongs to.""",
                                is_required=False,
                            ),
                            "jobId": Field(
                                String,
                                description="""Optional. The job ID, which must be unique within the
                                project.The ID must contain only letters (a-z, A-Z), numbers (0-9),
                                underscores (_), or hyphens (-). The maximum length is 100
                                characters.If not specified by the caller, the job ID will be
                                provided by the server.""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""Encapsulates the full scoping used to reference a job.""",
                    is_required=False,
                ),
                "hadoopJob": Field(
                    Shape(
                        fields={
                            "jarFileUris": Field(
                                [String],
                                description="""Optional. Jar file URIs to add to the CLASSPATHs of
                                the Hadoop driver and tasks.""",
                                is_required=False,
                            ),
                            "loggingConfig": Field(
                                Shape(
                                    fields={
                                        "driverLogLevels": Field(
                                            Permissive(),
                                            description="""The per-package log levels for the
                                            driver. This may include "root" package name to
                                            configure rootLogger. Examples:  \'com.google = FATAL\',
                                            \'root = INFO\', \'org.apache = DEBUG\'""",
                                            is_required=False,
                                        )
                                    }
                                ),
                                description="""The runtime logging config of the job.""",
                                is_required=False,
                            ),
                            "properties": Field(
                                Permissive(),
                                description="""Optional. A mapping of property names to values, used
                                to configure Hadoop. Properties that conflict with values set by the
                                Cloud Dataproc API may be overwritten. Can include properties set in
                                /etc/hadoop/conf/*-site and classes in user code.""",
                                is_required=False,
                            ),
                            "args": Field(
                                [String],
                                description="""Optional. The arguments to pass to the driver. Do not
                                include arguments, such as -libjars or -Dfoo=bar, that can be set as
                                job properties, since a collision may occur that causes an incorrect
                                job submission.""",
                                is_required=False,
                            ),
                            "fileUris": Field(
                                [String],
                                description="""Optional. HCFS (Hadoop Compatible Filesystem) URIs of
                                files to be copied to the working directory of Hadoop drivers and
                                distributed tasks. Useful for naively parallel tasks.""",
                                is_required=False,
                            ),
                            "mainClass": Field(
                                String,
                                description="""The name of the driver\'s main class. The jar file
                                containing the class must be in the default CLASSPATH or specified
                                in jar_file_uris.""",
                                is_required=False,
                            ),
                            "archiveUris": Field(
                                [String],
                                description="""Optional. HCFS URIs of archives to be extracted in
                                the working directory of Hadoop drivers and tasks. Supported file
                                types: .jar, .tar, .tar.gz, .tgz, or .zip.""",
                                is_required=False,
                            ),
                            "mainJarFileUri": Field(
                                String,
                                description="""The HCFS URI of the jar file containing the main
                                class. Examples:
                                \'gs://foo-bucket/analytics-binaries/extract-useful-metrics-mr.jar\'
                                \'hdfs:/tmp/test-samples/custom-wordcount.jar\'
                                \'file:///home/usr/lib/hadoop-mapreduce/hadoop-mapreduce-examples.jar\'""",
                                is_required=False,
                            ),
                        }
                    ),
                    description="""A Cloud Dataproc job for running Apache Hadoop MapReduce
                    (https://hadoop.apache.org/docs/current/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html)
                    jobs on Apache Hadoop YARN
                    (https://hadoop.apache.org/docs/r2.7.1/hadoop-yarn/hadoop-yarn-site/YARN.html).""",
                    is_required=False,
                ),
            }
        ),
        description="""A Cloud Dataproc job resource.""",
        is_required=False,
    )
