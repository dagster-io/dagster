import re
import subprocess

from threading import Thread
from six.moves import queue


def run_spark_subprocess(cmd, logger):
    """See https://bit.ly/2OpksJC for source of the subprocess stdout/stderr capture pattern in this
    function.
    """

    # Spark sometimes logs in log4j format. In those cases, we detect and parse.
    # Example log line from Spark that this is intended to match:
    # 2019-03-27 16:00:19 INFO  ContextHandler:781 - Started o.s.j.s.ServletContextHandler...
    log4j_regex = r'^(\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2}) ([A-Z]{3,5})(.*?)$'

    def reader(pipe, pipe_name, p, msg_queue):
        try:
            with pipe:
                while p.poll() is None:
                    for line in pipe.readlines():
                        match = re.match(log4j_regex, line)
                        if match:
                            line = match.groups()[2]
                        msg_queue.put((pipe_name, line))
        finally:
            # Use None as sentinel for done state, detected by iter() below
            msg_queue.put(None)

    p = subprocess.Popen(
        ' '.join(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        universal_newlines=True,
        shell=True,
    )
    q = queue.Queue()
    Thread(target=reader, args=[p.stdout, 'stdout', p, q]).start()
    Thread(target=reader, args=[p.stderr, 'stderr', p, q]).start()
    for _ in range(2):  # There will be two None sentinels, one for each stream
        for pipe_name, line in iter(q.get, None):
            if pipe_name == 'stdout':
                logger.info(line)
            elif pipe_name == 'stderr':
                logger.error(line)

    p.wait()
    return p.returncode
