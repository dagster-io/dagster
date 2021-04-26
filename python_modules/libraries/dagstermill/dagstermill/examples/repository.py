import os
import pickle
import uuid

import dagstermill
from dagster import (
    Field,
    FileHandle,
    InputDefinition,
    Int,
    List,
    ModeDefinition,
    OutputDefinition,
    ResourceDefinition,
    String,
    lambda_solid,
    pipeline,
    repository,
    resource,
    solid,
)
from dagster.core.storage.file_manager import local_file_manager
from dagster.utils import PICKLE_PROTOCOL, file_relative_path

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


def test_nb_solid(name, **kwargs):
    output_defs = kwargs.pop("output_defs", [OutputDefinition(is_required=False)])

    return dagstermill.define_dagstermill_solid(
        name=name,
        notebook_path=nb_test_path(name),
        output_notebook="notebook",
        output_defs=output_defs,
        **kwargs,
    )


default_mode_defs = [ModeDefinition(resource_defs={"file_manager": local_file_manager})]


hello_world = test_nb_solid("hello_world", output_defs=[])


@pipeline(mode_defs=default_mode_defs)
def hello_world_pipeline():
    hello_world()


hello_world_with_custom_tags_and_description = test_nb_solid(
    "hello_world", output_defs=[], tags={"foo": "bar"}, description="custom description"
)


@pipeline(mode_defs=default_mode_defs)
def hello_world_with_custom_tags_and_description_pipeline():
    hello_world_with_custom_tags_and_description()


hello_world_config = test_nb_solid(
    "hello_world_config",
    config_schema={"greeting": Field(String, is_required=False, default_value="hello")},
)


goodbye_config = dagstermill.define_dagstermill_solid(
    name="goodbye_config",
    notebook_path=nb_test_path("print_dagstermill_context_solid_config"),
    output_notebook="notebook",
    config_schema={"farewell": Field(String, is_required=False, default_value="goodbye")},
)


@pipeline(mode_defs=default_mode_defs)
def hello_world_config_pipeline():
    hello_world_config()
    goodbye_config()


@solid(input_defs=[InputDefinition("notebook", dagster_type=FileHandle)])
def load_notebook(_, notebook):
    return os.path.exists(notebook.path_desc)


@pipeline(mode_defs=default_mode_defs)
def hello_world_with_output_notebook_pipeline():
    notebook = hello_world()
    load_notebook(notebook)


hello_world_output = test_nb_solid("hello_world_output", output_defs=[OutputDefinition(str)])


@pipeline(mode_defs=default_mode_defs)
def hello_world_output_pipeline():
    hello_world_output()


hello_world_explicit_yield = test_nb_solid(
    "hello_world_explicit_yield", output_defs=[OutputDefinition(str)]
)


@pipeline(mode_defs=default_mode_defs)
def hello_world_explicit_yield_pipeline():
    hello_world_explicit_yield()


hello_logging = test_nb_solid("hello_logging")


@pipeline(mode_defs=default_mode_defs)
def hello_logging_pipeline():
    hello_logging()


add_two_numbers = test_nb_solid(
    "add_two_numbers",
    input_defs=[
        InputDefinition(name="a", dagster_type=Int),
        InputDefinition(name="b", dagster_type=Int),
    ],
    output_defs=[OutputDefinition(Int)],
)


mult_two_numbers = test_nb_solid(
    "mult_two_numbers",
    input_defs=[
        InputDefinition(name="a", dagster_type=Int),
        InputDefinition(name="b", dagster_type=Int),
    ],
    output_defs=[OutputDefinition(Int)],
)


@lambda_solid
def return_one():
    return 1


@lambda_solid
def return_two():
    return 2


@pipeline(mode_defs=default_mode_defs)
def add_pipeline():
    add_two_numbers(return_one(), return_two())


@solid(input_defs=[], config_schema=Int)
def load_constant(context):
    return context.solid_config


@pipeline(mode_defs=default_mode_defs)
def notebook_dag_pipeline():
    a = load_constant.alias("load_a")()
    b = load_constant.alias("load_b")()
    c, _ = add_two_numbers(a, b)
    mult_two_numbers(c, b)


error_notebook = test_nb_solid("error_notebook")


@pipeline(mode_defs=default_mode_defs)
def error_pipeline():
    error_notebook()


if DAGSTER_PANDAS_PRESENT and SKLEARN_PRESENT and MATPLOTLIB_PRESENT:

    clean_data = test_nb_solid("clean_data", output_defs=[OutputDefinition(DataFrame)])

    # FIXME add an output to this
    tutorial_LR = test_nb_solid(
        "tutorial_LR",
        input_defs=[InputDefinition(name="df", dagster_type=DataFrame)],
    )

    tutorial_RF = test_nb_solid(
        "tutorial_RF",
        input_defs=[InputDefinition(name="df", dagster_type=DataFrame)],
    )

    @pipeline(mode_defs=default_mode_defs)
    def tutorial_pipeline():
        df, _ = clean_data()
        # FIXME get better names for these
        tutorial_LR(df)
        tutorial_RF(df)


@solid("resource_solid", required_resource_keys={"list"})
def resource_solid(context):
    context.resources.list.append("Hello, solid!")
    return True


hello_world_resource = test_nb_solid(
    "hello_world_resource",
    input_defs=[InputDefinition("nonce")],
    required_resource_keys={"list"},
)

hello_world_resource_with_exception = test_nb_solid(
    "hello_world_resource_with_exception",
    input_defs=[InputDefinition("nonce")],
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
                "file_manager": local_file_manager,
            },
        ),
        ModeDefinition(
            name="prod",
            resource_defs={"list": filepicklelist_resource, "file_manager": local_file_manager},
        ),
    ]
)
def resource_pipeline():
    hello_world_resource(resource_solid())


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"list": filepicklelist_resource, "file_manager": local_file_manager}
        )
    ]
)
def resource_with_exception_pipeline():
    hello_world_resource_with_exception(resource_solid())


bad_kernel = test_nb_solid("bad_kernel")


@pipeline(mode_defs=default_mode_defs)
def bad_kernel_pipeline():
    bad_kernel()


reimport = test_nb_solid(
    "reimport", input_defs=[InputDefinition("l", List[int])], output_defs=[OutputDefinition(int)]
)


@solid
def lister(_):
    return [1, 2, 3]


@pipeline(mode_defs=default_mode_defs)
def reimport_pipeline():
    reimport(lister())


yield_3 = test_nb_solid("yield_3", output_defs=[OutputDefinition(Int)])


@pipeline(mode_defs=default_mode_defs)
def yield_3_pipeline():
    yield_3()


yield_obj = test_nb_solid("yield_obj")


@pipeline(mode_defs=default_mode_defs)
def yield_obj_pipeline():
    yield_obj()


@pipeline(mode_defs=default_mode_defs)
def retries_pipeline():
    test_nb_solid("raise_retry")()
    test_nb_solid("yield_retry")()


@pipeline(mode_defs=default_mode_defs)
def failure_pipeline():
    test_nb_solid("raise_failure")()
    test_nb_solid("yield_failure")()


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
    ]
    if DAGSTER_PANDAS_PRESENT and SKLEARN_PRESENT and MATPLOTLIB_PRESENT:
        pipelines += [tutorial_pipeline]

    return pipelines
