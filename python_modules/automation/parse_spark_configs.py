'''Spark config codegen.

This script parses the Spark configuration parameters downloaded from the Spark Github repository,
and codegens a file that contains dagster configurations for these parameters.
'''
import re

import requests
import pytablereader as ptr

from enum import Enum
from six import StringIO

from dagster.utils.indenting_printer import IndentingPrinter

import sys

SPARK_VERSION = "v2.4.0"
TABLE_REGEX = r"### (.{,30}?)\n\n(<table.*?>.*?<\/table>)"


class CONFIG_TYPE(Enum):
    STRING = 'String'
    INT = 'Int'
    FLOAT = 'Float'
    BOOL = 'Bool'
    MEMORY = 'String'  # TODO: We should handle memory field types
    TIME = 'String'  # TODO: We should handle time field types


CONFIG_TYPES = {
    #
    # APPLICATION PROPERTIES
    'spark.app.name': CONFIG_TYPE.STRING,
    'spark.driver.cores': CONFIG_TYPE.INT,
    'spark.driver.maxResultSize': CONFIG_TYPE.MEMORY,
    'spark.driver.memory': CONFIG_TYPE.MEMORY,
    'spark.driver.memoryOverhead': CONFIG_TYPE.MEMORY,
    'spark.executor.memory': CONFIG_TYPE.MEMORY,
    'spark.executor.pyspark.memory': CONFIG_TYPE.MEMORY,
    'spark.executor.memoryOverhead	': CONFIG_TYPE.MEMORY,
    'spark.extraListeners': CONFIG_TYPE.STRING,
    'spark.local.dir': CONFIG_TYPE.STRING,
    'spark.logConf': CONFIG_TYPE.BOOL,
    # TODO: Validate against https://spark.apache.org/docs/latest/submitting-applications.html#master-urls
    'spark.master': CONFIG_TYPE.STRING,
    # TODO: Validate against client/cluster *only*.
    'spark.submit.deployMode': CONFIG_TYPE.STRING,
    'spark.log.callerContext': CONFIG_TYPE.STRING,
    'spark.driver.supervise': CONFIG_TYPE.BOOL,
    #
    # RUNTIME ENVIRONMENT
    'spark.driver.extraClassPath': CONFIG_TYPE.STRING,
    'spark.driver.extraJavaOptions': CONFIG_TYPE.STRING,
    'spark.driver.extraLibraryPath': CONFIG_TYPE.STRING,
    'spark.driver.userClassPathFirst': CONFIG_TYPE.BOOL,
    'spark.executor.extraClassPath': CONFIG_TYPE.STRING,
    'spark.executor.extraJavaOptions': CONFIG_TYPE.STRING,
    'spark.executor.extraLibraryPath': CONFIG_TYPE.STRING,
    'spark.executor.logs.rolling.maxRetainedFiles': CONFIG_TYPE.INT,
    'spark.executor.logs.rolling.enableCompression': CONFIG_TYPE.BOOL,
    'spark.executor.logs.rolling.maxSize': CONFIG_TYPE.INT,
    # TODO: Can only be 'time' or 'size'
    'spark.executor.logs.rolling.strategy': CONFIG_TYPE.STRING,
    'spark.executor.logs.rolling.time.interval': CONFIG_TYPE.STRING,
    'spark.executor.userClassPathFirst': CONFIG_TYPE.BOOL,
    'spark.redaction.regex': CONFIG_TYPE.STRING,
    'spark.python.profile': CONFIG_TYPE.BOOL,
    # TODO: Should be a path?
    'spark.python.profile.dump': CONFIG_TYPE.STRING,
    'spark.python.worker.memory': CONFIG_TYPE.MEMORY,
    'spark.python.worker.reuse': CONFIG_TYPE.BOOL,
    'spark.files': CONFIG_TYPE.STRING,
    'spark.submit.pyFiles': CONFIG_TYPE.STRING,
    'spark.jars': CONFIG_TYPE.STRING,
    'spark.jars.packages': CONFIG_TYPE.STRING,
    'spark.jars.excludes': CONFIG_TYPE.STRING,
    'spark.jars.ivy': CONFIG_TYPE.STRING,
    'spark.jars.ivySettings': CONFIG_TYPE.STRING,
    'spark.jars.repositories': CONFIG_TYPE.STRING,
    'spark.pyspark.driver.python': CONFIG_TYPE.STRING,
    'spark.pyspark.python': CONFIG_TYPE.STRING,
    #
    # SHUFFLE BEHAVIOR
    'spark.reducer.maxSizeInFlight': CONFIG_TYPE.MEMORY,
    'spark.reducer.maxReqsInFlight': CONFIG_TYPE.INT,
    'spark.reducer.maxBlocksInFlightPerAddress': CONFIG_TYPE.INT,
    'spark.maxRemoteBlockSizeFetchToMem': CONFIG_TYPE.INT,
    'spark.shuffle.compress': CONFIG_TYPE.BOOL,
    'spark.shuffle.file.buffer': CONFIG_TYPE.MEMORY,
    'spark.shuffle.io.maxRetries': CONFIG_TYPE.INT,
    'spark.shuffle.io.numConnectionsPerPeer': CONFIG_TYPE.INT,
    'spark.shuffle.io.preferDirectBufs': CONFIG_TYPE.BOOL,
    'spark.shuffle.io.retryWait': CONFIG_TYPE.TIME,
    'spark.shuffle.service.enabled': CONFIG_TYPE.BOOL,
    'spark.shuffle.service.port': CONFIG_TYPE.INT,
    'spark.shuffle.service.index.cache.size': CONFIG_TYPE.MEMORY,
    'spark.shuffle.maxChunksBeingTransferred': CONFIG_TYPE.INT,
    'spark.shuffle.sort.bypassMergeThreshold': CONFIG_TYPE.INT,
    'spark.shuffle.spill.compress': CONFIG_TYPE.BOOL,
    'spark.shuffle.accurateBlockThreshold': CONFIG_TYPE.INT,
    'spark.shuffle.registration.timeout': CONFIG_TYPE.INT,
    'spark.shuffle.registration.maxAttempts': CONFIG_TYPE.INT,
    #
    # SPARK UI
    ### TODO
    #
    # COMPRESSION AND SERIALIZATION
    ### TODO
    #
    # MEMORY MANAGEMENT
    'spark.memory.fraction': CONFIG_TYPE.FLOAT,
    'spark.memory.storageFraction': CONFIG_TYPE.FLOAT,
    'spark.memory.offHeap.enabled': CONFIG_TYPE.BOOL,
    'spark.memory.offHeap.size': CONFIG_TYPE.INT,
    'spark.memory.useLegacyMode': CONFIG_TYPE.BOOL,
    'spark.shuffle.memoryFraction': CONFIG_TYPE.FLOAT,
    'spark.storage.memoryFraction': CONFIG_TYPE.FLOAT,
    'spark.storage.unrollFraction': CONFIG_TYPE.FLOAT,
    'spark.storage.replication.proactive': CONFIG_TYPE.BOOL,
    'spark.cleaner.periodicGC.interval': CONFIG_TYPE.TIME,
    'spark.cleaner.referenceTracking': CONFIG_TYPE.BOOL,
    'spark.cleaner.referenceTracking.blocking': CONFIG_TYPE.BOOL,
    'spark.cleaner.referenceTracking.blocking.shuffle': CONFIG_TYPE.BOOL,
    'spark.cleaner.referenceTracking.cleanCheckpoints': CONFIG_TYPE.BOOL,
    #
    # EXECUTION BEHAVIOR
    'spark.broadcast.blockSize': CONFIG_TYPE.MEMORY,
    'spark.executor.cores': CONFIG_TYPE.INT,
    'spark.default.parallelism': CONFIG_TYPE.INT,
    'spark.executor.heartbeatInterval': CONFIG_TYPE.TIME,
    'spark.files.fetchTimeout': CONFIG_TYPE.TIME,
    'spark.files.useFetchCache': CONFIG_TYPE.BOOL,
    'spark.files.overwrite': CONFIG_TYPE.BOOL,
    'spark.files.maxPartitionBytes': CONFIG_TYPE.INT,
    'spark.files.openCostInBytes': CONFIG_TYPE.INT,
    'spark.hadoop.cloneConf': CONFIG_TYPE.BOOL,
    'spark.hadoop.validateOutputSpecs': CONFIG_TYPE.BOOL,
    'spark.storage.memoryMapThreshold': CONFIG_TYPE.MEMORY,
    # TODO: Can only be 1 or 2.
    'spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version': CONFIG_TYPE.INT,
    #
    # NETWORKING
    ### TODO
    #
    # SCHEDULING
    ### TODO
    #
    # DYNAMIC ALLOCATION
    ### TODO
}


class IndentingBufferPrinter(IndentingPrinter):
    '''Subclass of IndentingPrinter wrapping a StringIO.'''

    def __init__(self, indent_level=4, current_indent=0):
        self.buffer = StringIO()
        self.printer = lambda x: self.buffer.write(x + '\n')
        super(IndentingBufferPrinter, self).__init__(
            indent_level=indent_level, printer=self.printer, current_indent=current_indent
        )

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self.buffer.close()

    def read(self):
        '''Get the value of the backing StringIO.'''
        return self.buffer.getvalue()


class SparkConfig:
    def __init__(self, path, default, meaning):
        self.path = path

        # The original documentation strings include extraneous newlines, spaces
        WHITESPACE_REGEX = r'\s+'
        self.default = re.sub(WHITESPACE_REGEX, ' ', str(default)).strip()
        self.meaning = re.sub(WHITESPACE_REGEX, ' ', meaning).strip()

    @property
    def split_path(self):
        return self.path.split('.')

    def print(self, printer):
        config_type = CONFIG_TYPES.get(self.path, CONFIG_TYPE.STRING).value

        printer.append('Field(')
        with printer.with_indent():
            printer.line('')
            printer.line('{},'.format(config_type))
            printer.append("description='''")
            printer.append(self.meaning)
            printer.line("''',")
            # printer.line("default_value='{}',".format(self.default))
            printer.line('is_optional=True,')

        printer.append(')')


class SparkConfigNode:
    def __init__(self, value=None):
        self.value = value
        self.children = {}

    def print(self, printer):
        if not self.children:
            self.value.print(printer)
        else:
            if self.value:
                retdict = {'root': self.value}
                retdict.update(self.children)
            else:
                retdict = self.children

            printer.append('Field(')
            printer.line('')
            with printer.with_indent():
                printer.line('PermissiveDict(')
                with printer.with_indent():
                    printer.line('fields={')
                    with printer.with_indent():
                        for i, (k, v) in enumerate(retdict.items()):
                            with printer.with_indent():
                                printer.append("'{}': ".format(k))
                            v.print(printer)

                            printer.line(',')
                    printer.line('}')
                printer.line(')')
            printer.line(')')
        return printer.read()


def main():
    r = requests.get(
        'https://raw.githubusercontent.com/apache/spark/{}/docs/configuration.md'.format(
            SPARK_VERSION
        )
    )

    tables = re.findall(TABLE_REGEX, r.text, re.DOTALL | re.MULTILINE)

    spark_configs = []
    for name, table in tables:
        parsed_table = list(ptr.HtmlTableTextLoader(table).load())[0]
        df = parsed_table.as_dataframe()
        for _, row in df.iterrows():
            s = SparkConfig(row['Property Name'], row['Default'], name + ": " + row['Meaning'])
            spark_configs.append(s)

    result = SparkConfigNode()
    for s in spark_configs:
        # TODO: we should handle this thing
        if s.path == 'spark.executorEnv.[EnvironmentVariableName]':
            continue

        print(s.path, file=sys.stderr)
        key_path = s.split_path
        d = result
        while key_path:
            key = key_path.pop(0)
            if key not in d.children:
                d.children[key] = SparkConfigNode()
            d = d.children[key]
        d.value = s

    with IndentingBufferPrinter() as printer:
        printer.line("'''NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT")
        printer.blank_line()
        printer.line("'''")
        printer.blank_line()
        printer.blank_line()
        printer.line('from dagster import Bool, Field, Float, Int, PermissiveDict, String')
        printer.blank_line()
        printer.blank_line()
        printer.line('def spark_config():')
        with printer.with_indent():
            printer.append('return ')
            result.print(printer)
            print(printer.read())


if __name__ == "__main__":
    main()
