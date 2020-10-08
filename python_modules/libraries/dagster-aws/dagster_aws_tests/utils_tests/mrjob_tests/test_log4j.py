from dagster_aws.utils.mrjob.log4j import Log4jRecord, parse_hadoop_log4j_records

SIMPLE_LOG4J = """
20/02/05 17:26:43 INFO SparkContext: Running Spark version 2.4.4
20/02/05 17:26:43 INFO SparkContext: Submitted application: blah
20/02/05 17:26:43 INFO SecurityManager: Changing view acls to: hadoop
""".strip()

MULTILINE_LOG4J = """
20/02/05 17:26:50 INFO Client: Application report for application_1580918830280_0002 (state: ACCEPTED)
20/02/05 17:26:50 INFO Client:
         client token: N/A
         diagnostics: AM container is launched, waiting for AM container to Register with RM
         ApplicationMaster host: N/A
         ApplicationMaster RPC port: -1
         queue: default
         start time: 1580923609467
         final status: UNDEFINED
         tracking URL: http://ip-172-31-2-74.us-west-1.compute.internal:20888/proxy/application_1580918830280_0002/
         user: hadoop
20/02/05 17:26:51 INFO Client: Application report for application_1580918830280_0002 (state: ACCEPTED)
""".strip()


def test_simple_log4j_parsing():
    res = parse_hadoop_log4j_records(SIMPLE_LOG4J)
    expected = [
        Log4jRecord(
            caller_location="",
            level="INFO",
            logger="SparkContext",
            message="Running Spark version 2.4.4",
            num_lines=1,
            start_line=0,
            thread=None,
            timestamp="20/02/05 17:26:43",
        ),
        Log4jRecord(
            caller_location="",
            level="INFO",
            logger="SparkContext",
            message="Submitted application: blah",
            num_lines=1,
            start_line=1,
            thread=None,
            timestamp="20/02/05 17:26:43",
        ),
        Log4jRecord(
            caller_location="",
            level="INFO",
            logger="SecurityManager",
            message="Changing view acls to: hadoop",
            num_lines=1,
            start_line=2,
            thread=None,
            timestamp="20/02/05 17:26:43",
        ),
    ]
    assert list(res) == expected


def test_multiline_log4j_parsing():
    res = parse_hadoop_log4j_records(MULTILINE_LOG4J)

    expected = [
        Log4jRecord(
            caller_location="",
            level="INFO",
            logger="Client",
            message="Application report for application_1580918830280_0002 (state: ACCEPTED)",
            num_lines=1,
            start_line=0,
            thread=None,
            timestamp="20/02/05 17:26:50",
        ),
        Log4jRecord(
            caller_location="",
            level="INFO",
            logger="Client",
            message="\n".join(
                [
                    "",
                    "         client token: N/A",
                    "         diagnostics: AM container is launched, waiting for AM container to Register with RM",
                    "         ApplicationMaster host: N/A",
                    "         ApplicationMaster RPC port: -1",
                    "         queue: default",
                    "         start time: 1580923609467",
                    "         final status: UNDEFINED",
                    "         tracking URL: http://ip-172-31-2-74.us-west-1.compute.internal:20888/proxy/application_1580918830280_0002/",
                    "         user: hadoop",
                ]
            ),
            num_lines=10,
            start_line=1,
            thread=None,
            timestamp="20/02/05 17:26:50",
        ),
        Log4jRecord(
            caller_location="",
            level="INFO",
            logger="Client",
            message="Application report for application_1580918830280_0002 (state: ACCEPTED)",
            num_lines=1,
            start_line=11,
            thread=None,
            timestamp="20/02/05 17:26:51",
        ),
    ]
    assert list(res) == expected
