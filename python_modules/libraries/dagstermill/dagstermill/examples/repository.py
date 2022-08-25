import os
import pickle
import uuid

import dagstermill
from dagstermill.io_managers import local_output_notebook_io_manager

from dagster import (
    Field,
    FileHandle,
    In,
    Int,
    List,
    Out,
    ResourceDefinition,
    String,
    fs_io_manager,
    job,
    repository,
    resource,
)
from dagster._core.definitions.utils import DEFAULT_OUTPUT
from dagster._core.storage.file_manager import local_file_manager
from dagster._legacy import InputDefinition, ModeDefinition, composite_solid, pipeline, solid
from dagster._utils import PICKLE_PROTOCOL, file_relative_path

try:
    from dagster_pandas import DataFrame

    DAGSTER_PANDAS_PRESENT = True
except ImportError:
    DAGSTER_PANDAS_PRESENT = False

try:
    import sklearn as _

    SKLEARN_PRESENT = True
except ImportError:
    SKLEARN_PRESENT = False

try:
    import matplotlib as _

    MATPLOTLIB_PRESENT = True
except ImportError:
    MATPLOTLIB_PRESENT = False


class BasicTest:
    def __init__(self, x):
        self.x = x

    def __repr__(self):
        return "BasicTest: {x}".format(x=str(self.x))


def nb_test_path(name):
    return file_relative_path(__file__, f"notebooks/{name}.ipynb")


def test_nb_op(name, **kwargs):
    outs = kwargs.pop("outs", {DEFAULT_OUTPUT: Out(is_required=False)})
    path = kwargs.pop("path", nb_test_path(name))

    return dagstermill.define_dagstermill_op(
        name=name,
        notebook_path=path,
        output_notebook_name="notebook",
        outs=outs,
        **kwargs,
    )


default_mode_defs = [
    ModeDefinition(
        resource_defs={
            "output_notebook_io_manager": local_output_notebook_io_manager,
            "io_manager": fs_io_manager,
        }
    )
]


hello_world = test_nb_op("hello_world", outs={})


@pipeline(mode_defs=default_mode_defs)
def hello_world_pipeline():
    hello_world()


hello_world_op = test_nb_op(
    "hello_world_op",
    path=nb_test_path("hello_world"),
    outs={},
)


def build_hello_world_job():
    @job(
        resource_defs={
            "output_notebook_io_manager": local_output_notebook_io_manager,
        }
    )
    def hello_world_job():
        hello_world_op()

    return hello_world_job


hello_world_with_custom_tags_and_description = dagstermill.factory.define_dagstermill_solid(
    name="hello_world_custom",
    notebook_path=nb_test_path("hello_world"),
    output_notebook_name="notebook",
    tags={"foo": "bar"},
    description="custom description",
)


@pipeline(mode_defs=default_mode_defs)
def hello_world_with_custom_tags_and_description_pipeline():
    hello_world_with_custom_tags_and_description()


hello_world_config = test_nb_op(
    "hello_world_config",
    config_schema={"greeting": Field(String, is_required=False, default_value="hello")},
)


goodbye_config = dagstermill.factory.define_dagstermill_solid(
    name="goodbye_config",
    notebook_path=nb_test_path("print_dagstermill_context_solid_config"),
    output_notebook_name="notebook",
    config_schema={"farewell": Field(String, is_required=False, default_value="goodbye")},
)


@pipeline(mode_defs=default_mode_defs)
def hello_world_config_pipeline():
    hello_world_config()
    goodbye_config()


@pipeline(mode_defs=default_mode_defs)
def alias_config_pipeline():
    hello_world_config.alias("aliased_greeting")()
    goodbye_config.alias("aliased_goodbye")()


@solid(input_defs=[InputDefinition("notebook")])
def load_notebook(notebook):
    return notebook


@pipeline(mode_defs=default_mode_defs)
def hello_world_with_output_notebook_pipeline():
    notebook = hello_world()
    load_notebook(notebook)


hello_world_no_output_notebook_no_file_manager = dagstermill.factory.define_dagstermill_solid(
    name="hello_world_no_output_notebook_no_file_manager",
    notebook_path=nb_test_path("hello_world"),
)


@pipeline
def hello_world_no_output_notebook_no_file_manager_pipeline():
    hello_world_no_output_notebook_no_file_manager()


hello_world_no_output_notebook = dagstermill.factory.define_dagstermill_solid(
    name="hello_world_no_output_notebook",
    notebook_path=nb_test_path("hello_world"),
)


@pipeline(mode_defs=default_mode_defs)
def hello_world_no_output_notebook_pipeline():
    hello_world_no_output_notebook()


hello_world_output = test_nb_op("hello_world_output", outs={DEFAULT_OUTPUT: Out(str)})


@pipeline(mode_defs=default_mode_defs)
def hello_world_output_pipeline():
    hello_world_output()


hello_world_explicit_yield = test_nb_op(
    "hello_world_explicit_yield", outs={DEFAULT_OUTPUT: Out(str)}
)


@pipeline(mode_defs=default_mode_defs)
def hello_world_explicit_yield_pipeline():
    hello_world_explicit_yield()


hello_logging = test_nb_op("hello_logging")


@pipeline(mode_defs=default_mode_defs)
def hello_logging_pipeline():
    hello_logging()


add_two_numbers = test_nb_op(
    "add_two_numbers",
    ins={"a": In(int), "b": In(int)},
    outs={DEFAULT_OUTPUT: Out(int)},
)


mult_two_numbers = test_nb_op(
    "mult_two_numbers", ins={"a": In(int), "b": In(int)}, outs={DEFAULT_OUTPUT: Out(int)}
)


@solid
def return_one():
    return 1


@solid
def return_two():
    return 2


@solid
def return_three():
    return 3


@solid
def return_four():
    return 4


@pipeline(mode_defs=default_mode_defs)
def add_pipeline():
    add_two_numbers(return_one(), return_two())


@pipeline(mode_defs=default_mode_defs)
def double_add_pipeline():
    add_two_numbers.alias("add_two_numbers_1")(return_one(), return_two())
    add_two_numbers.alias("add_two_numbers_2")(return_three(), return_four())


@solid(input_defs=[], config_schema=Int)
def load_constant(context):
    return context.solid_config


@pipeline(mode_defs=default_mode_defs)
def notebook_dag_pipeline():
    a = load_constant.alias("load_a")()
    b = load_constant.alias("load_b")()
    num, _ = add_two_numbers(a, b)
    mult_two_numbers(num, b)


error_notebook = test_nb_op("error_notebook")


@pipeline(mode_defs=default_mode_defs)
def error_pipeline():
    error_notebook()


if DAGSTER_PANDAS_PRESENT and SKLEARN_PRESENT and MATPLOTLIB_PRESENT:

    clean_data = test_nb_op("clean_data", outs={DEFAULT_OUTPUT: Out(DataFrame)})

    # FIXME add an output to this
    tutorial_LR = test_nb_op("tutorial_LR", ins={"df": In(DataFrame)})

    tutorial_RF = test_nb_op("tutorial_RF", ins={"df": In(DataFrame)})

    @pipeline(mode_defs=default_mode_defs)
    def tutorial_pipeline():
        dfr, _ = clean_data()
        # FIXME get better names for these
        tutorial_LR(dfr)
        tutorial_RF(dfr)


@solid("resource_solid", required_resource_keys={"list"})
def resource_solid(context):
    context.resources.list.append("Hello, solid!")
    return True


hello_world_resource = test_nb_op(
    "hello_world_resource",
    ins={"nonce": In()},
    required_resource_keys={"list"},
)

hello_world_resource_with_exception = test_nb_op(
    "hello_world_resource_with_exception",
    ins={"nonce": In()},
    required_resource_keys={"list"},
)


class FilePickleList:
    # This is not thread- or anything else-safe
    def __init__(self, path):
        self.closed = False
        self.id = str(uuid.uuid4())[-6:]
        self.path = path
        self.list = []
        if not os.path.exists(self.path):
            self.write()
        self.read()
        self.open()

    def open(self):
        self.read()
        self.append("Opened")

    def append(self, obj):
        self.read()
        self.list.append(self.id + ": " + obj)
        self.write()

    def read(self):
        with open(self.path, "rb") as fd:
            self.list = pickle.load(fd)
            return self.list

    def write(self):
        with open(self.path, "wb") as fd:
            pickle.dump(self.list, fd, protocol=PICKLE_PROTOCOL)

    def close(self):
        self.append("Closed")
        self.closed = True


@resource(config_schema=Field(String))
def filepicklelist_resource(init_context):
    filepicklelist = FilePickleList(init_context.resource_config)
    try:
        yield filepicklelist
    finally:
        filepicklelist.close()


@pipeline(
    mode_defs=[
        ModeDefinition(
            name="test",
            resource_defs={
                "list": ResourceDefinition(lambda _: []),
                "io_manager": fs_io_manager,
                "output_notebook_io_manager": local_output_notebook_io_manager,
            },
        ),
        ModeDefinition(
            name="prod",
            resource_defs={
                "list": filepicklelist_resource,
                "output_notebook_io_manager": local_output_notebook_io_manager,
                "io_manager": fs_io_manager,
            },
        ),
    ]
)
def resource_pipeline():
    hello_world_resource(resource_solid())


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={
                "list": filepicklelist_resource,
                "output_notebook_io_manager": local_output_notebook_io_manager,
                "io_manager": fs_io_manager,
            }
        )
    ]
)
def resource_with_exception_pipeline():
    hello_world_resource_with_exception(resource_solid())


bad_kernel = test_nb_op("bad_kernel")


@pipeline(mode_defs=default_mode_defs)
def bad_kernel_pipeline():
    bad_kernel()


reimport = test_nb_op("reimport", ins={"l": In(List[int])}, outs={DEFAULT_OUTPUT: Out(int)})


@solid
def lister():
    return [1, 2, 3]


@pipeline(mode_defs=default_mode_defs)
def reimport_pipeline():
    reimport(lister())


yield_3 = test_nb_op("yield_3", outs={DEFAULT_OUTPUT: Out(int)})


@pipeline(mode_defs=default_mode_defs)
def yield_3_pipeline():
    yield_3()


yield_obj = test_nb_op("yield_obj")


@pipeline(mode_defs=default_mode_defs)
def yield_obj_pipeline():
    yield_obj()


@pipeline(mode_defs=default_mode_defs)
def retries_pipeline():
    test_nb_op("raise_retry")()
    test_nb_op("yield_retry")()


@pipeline(mode_defs=default_mode_defs)
def failure_pipeline():
    test_nb_op("raise_failure")()
    test_nb_op("yield_failure")()


yield_something = test_nb_op(
    "yield_something", ins={"obj": In(str)}, outs={DEFAULT_OUTPUT: Out(str)}
)


@solid
def fan_in(a, b):
    return f"{a} {b}"


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={
                "io_manager": fs_io_manager,
                "output_notebook_io_manager": local_output_notebook_io_manager,
            }
        )
    ]
)
def fan_in_notebook_pipeline():
    val_a, _ = yield_something.alias("solid_1")()
    val_b, _ = yield_something.alias("solid_2")()
    fan_in(val_a, val_b)


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={
                "output_notebook_io_manager": local_output_notebook_io_manager,
            }
        )
    ]
)
def fan_in_notebook_pipeline_in_mem():
    val_a, _ = yield_something.alias("solid_1")()
    val_b, _ = yield_something.alias("solid_2")()
    fan_in(val_a, val_b)


@composite_solid
def outer():
    yield_something()


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={
                "io_manager": fs_io_manager,
                "output_notebook_io_manager": local_output_notebook_io_manager,
            }
        )
    ]
)
def composite_pipeline():
    outer()


###################################################################################################
# Back compat
###################################################################################################

hello_world_legacy = dagstermill.factory.define_dagstermill_solid(
    name="hello_world_legacy",
    notebook_path=nb_test_path("hello_world"),
    output_notebook="notebook",
)


@solid(input_defs=[InputDefinition("notebook", dagster_type=FileHandle)])
def load_notebook_legacy(notebook):
    return os.path.exists(notebook.path_desc)


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={
                "io_manager": fs_io_manager,
                "file_manager": local_file_manager,
            }
        )
    ]
)
def hello_world_with_output_notebook_pipeline_legacy():
    notebook = hello_world_legacy()
    load_notebook_legacy(notebook)


@repository
def notebook_repo():
    pipelines = [
        bad_kernel_pipeline,
        error_pipeline,
        hello_world_pipeline,
        hello_world_with_custom_tags_and_description_pipeline,
        hello_world_config_pipeline,
        hello_world_explicit_yield_pipeline,
        hello_world_output_pipeline,
        hello_world_with_output_notebook_pipeline,
        hello_logging_pipeline,
        resource_pipeline,
        resource_with_exception_pipeline,
        add_pipeline,
        notebook_dag_pipeline,
        reimport_pipeline,
        yield_3_pipeline,
        yield_obj_pipeline,
        retries_pipeline,
        failure_pipeline,
        fan_in_notebook_pipeline_in_mem,
        fan_in_notebook_pipeline,
        hello_world_no_output_notebook_no_file_manager_pipeline,
        hello_world_with_output_notebook_pipeline_legacy,
    ]
    if DAGSTER_PANDAS_PRESENT and SKLEARN_PRESENT and MATPLOTLIB_PRESENT:
        pipelines += [tutorial_pipeline]

    return pipelines
