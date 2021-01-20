# -*- coding: utf-8 -*-
# Copyright 2015-2016 Yelp
# Copyright 2019 Yelp
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Parse the log4j syslog format used by Hadoop."""
import re
from collections import namedtuple

# log line format output by hadoop jar command
_HADOOP_LOG4J_LINE_RE = re.compile(
    r"^\s*(?P<timestamp>\d\d\/\d\d\/\d\d \d\d\:\d\d\:\d\d)"
    r"\s+(?P<level>[A-Z]+)"
    r"\s+(?P<logger>\S+)"
    r"(\s+\((?P<thread>.*?)\))?"
    r"( - ?|: ?)"
    r"(?P<message>.*?)$"
)

# log line format output to Hadoop syslog
_HADOOP_LOG4J_LINE_ALTERNATE_RE = re.compile(
    r"^\s*(?P<timestamp>\d\d\/\d\d\/\d\d \d\d\:\d\d\:\d\d)"
    r"\s+(?P<level>[A-Z]+)"
    r"(\s+\[(?P<thread>.*?)\])"
    r"\s+(?P<logger>\S+)"
    r"(\s+\((?P<caller_location>\S+)\))?"
    r"( - ?|: ?)"
    r"(?P<message>.*?)$"
)


class Log4jRecord(
    namedtuple(
        "_Log4jRecord", "caller_location level logger message num_lines start_line thread timestamp"
    )
):
    """Represents a Log4J log record.

    caller_location -- e.g. 'YarnClientImpl.java:submitApplication(251)'
    level -- e.g. 'INFO'
    logger -- e.g. 'amazon.emr.metrics.MetricsSaver'
    message -- the actual message. If this is a multi-line message (e.g.
        for counters), the lines will be joined by '\n'
    num_lines -- how many lines made up the message
    start_line -- which line the message started on (0-indexed)
    thread -- e.g. 'main'. Defaults to ''
    timestamp -- unparsed timestamp, e.g. '15/12/07 20:49:28'
    """

    def __new__(
        cls, caller_location, level, logger, message, num_lines, start_line, thread, timestamp
    ):
        return super(Log4jRecord, cls).__new__(
            cls, caller_location, level, logger, message, num_lines, start_line, thread, timestamp
        )

    @staticmethod
    def fake_record(line, line_num):
        """Used to represent a leading Log4J line that doesn't conform to the regular expressions we
        expect.
        """
        return Log4jRecord(
            caller_location="",
            level="",
            logger="",
            message=line,
            num_lines=1,
            start_line=line_num,
            thread="",
            timestamp="",
        )


def parse_hadoop_log4j_records(lines):
    """Parse lines from a hadoop log into log4j records.

    Yield Log4jRecords.

    Lines will be converted to unicode, and trailing \r and \n will be stripped
    from lines.

    Also yields fake records for leading non-log4j lines (trailing non-log4j
    lines are assumed to be part of a multiline message if not pre-filtered).
    """
    last_record = None
    line_num = 0

    for line_num, line in enumerate(lines.split("\n")):
        # convert from bytes to unicode, if needed, and strip trailing newlines
        line = line.rstrip("\r\n")

        m = _HADOOP_LOG4J_LINE_RE.match(line) or _HADOOP_LOG4J_LINE_ALTERNATE_RE.match(line)

        if m:
            if last_record:
                last_record = last_record._replace(num_lines=line_num - last_record.start_line)
                yield last_record

            matches = m.groupdict()

            last_record = Log4jRecord(
                caller_location=matches.get("caller_location", ""),
                level=matches["level"],
                logger=matches["logger"],
                message=matches["message"],
                num_lines=1,
                start_line=line_num,
                thread=matches.get("thread", ""),
                timestamp=matches["timestamp"],
            )
        else:
            # add on to previous record
            if last_record:
                last_record = last_record._replace(message=last_record.message + "\n" + line)
            else:
                yield Log4jRecord.fake_record(line, line_num)

    if last_record:
        last_record = last_record._replace(num_lines=line_num + 1 - last_record.start_line)
        yield last_record
