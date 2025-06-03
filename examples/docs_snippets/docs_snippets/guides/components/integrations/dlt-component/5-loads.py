import dlt


@dlt.source
def my_source():
    @dlt.resource
    def hello_world():
        yield "hello, world!"

    return hello_world


my_load_source = my_source()
my_load_pipeline = dlt.pipeline(destination="snowflake")
