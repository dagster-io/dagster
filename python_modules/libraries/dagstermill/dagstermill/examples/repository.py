import os
import pickle
import uuid

from dagster import (
    AssetIn,
    AssetSelection,
    Field,
    In,
    Int,
    List,
    Out,
    ResourceDefinition,
    String,
    asset,
    define_asset_job,
    fs_io_manager,
    graph,
    job,
    mem_io_manager,
    op,
    repository,
    resource,
    with_resources,
)
from dagster._core.definitions.utils import DEFAULT_OUTPUT
from dagster._utils import PICKLE_PROTOCOL, file_relative_path

import dagstermill
from dagstermill.io_managers import local_output_notebook_io_manager

try:
    from dagster_pandas import DataFrame

    DAGSTER_PANDAS_PRESENT = True
except ImportError:
    DAGSTER_PANDAS_PRESENT = False

try:
    import sklearn  # noqa: F401

    SKLEARN_PRESENT = True
except ImportError:
    SKLEARN_PRESENT = False

try:
    import matplotlib  # noqa: F401

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
    output_nb_name = kwargs.pop("output_notebook_name", "notebook")

    return dagstermill.define_dagstermill_op(
        name=name,
        notebook_path=path,
        output_notebook_name=output_nb_name,
        outs=outs,
        **kwargs,
    )


common_resource_defs = {
    "output_notebook_io_manager": local_output_notebook_io_manager,
    "io_manager": fs_io_manager,  # TODO check if necessary
}

hello_world = test_nb_op("hello_world", outs={})


@job(resource_defs=common_resource_defs)
def hello_world_job():
    hello_world()


def build_hello_world_job():
    @job(
        resource_defs={
            "output_notebook_io_manager": local_output_notebook_io_manager,
        }
    )
    def hello_world_job():
        hello_world()

    return hello_world_job


hello_world_with_custom_tags_and_description = test_nb_op(
    name="hello_world_custom",
    path=nb_test_path("hello_world"),
    output_notebook_name="notebook",
    tags={"foo": "bar"},
    description="custom description",
)


@job(resource_defs=common_resource_defs)
def hello_world_with_custom_tags_and_description_job():
    hello_world_with_custom_tags_and_description()


hello_world_config = test_nb_op(
    "hello_world_config",
    config_schema={"greeting": Field(String, is_required=False, default_value="hello")},
)


goodbye_config = test_nb_op(
    name="goodbye_config",
    path=nb_test_path("print_dagstermill_context_op_config"),
    output_notebook_name="notebook",
    config_schema={"farewell": Field(String, is_required=False, default_value="goodbye")},
)


@job(resource_defs=common_resource_defs)
def hello_world_config_job():
    hello_world_config()
    goodbye_config()


@job(resource_defs=common_resource_defs)
def alias_config_job():
    hello_world_config.alias("aliased_greeting")()
    goodbye_config.alias("aliased_goodbye")()


@op(ins={"notebook": In()})
def load_notebook(notebook):
    return notebook


@job(resource_defs=common_resource_defs)
def hello_world_with_output_notebook_job():
    notebook = hello_world()
    load_notebook(notebook)


hello_world_no_output_notebook = test_nb_op(
    name="hello_world_no_output_notebook",
    path=nb_test_path("hello_world"),
    output_notebook_name=None,
)


@job
def hello_world_no_output_notebook_no_file_manager_job():
    hello_world_no_output_notebook()


@job(resource_defs=common_resource_defs)
def hello_world_no_output_notebook_job():
    hello_world_no_output_notebook()


hello_world_output = test_nb_op("hello_world_output", outs={DEFAULT_OUTPUT: Out(str)})


@job(resource_defs=common_resource_defs)
def hello_world_output_job():
    hello_world_output()


hello_world_explicit_yield = test_nb_op(
    "hello_world_explicit_yield", outs={DEFAULT_OUTPUT: Out(str)}
)


@job(resource_defs=common_resource_defs)
def hello_world_explicit_yield_job():
    hello_world_explicit_yield()


hello_logging = test_nb_op("hello_logging")


@job(resource_defs=common_resource_defs)
def hello_logging_job():
    hello_logging()


add_two_numbers = test_nb_op(
    "add_two_numbers",
    ins={"a": In(int), "b": In(int)},
    outs={DEFAULT_OUTPUT: Out(int)},
)


mult_two_numbers = test_nb_op(
    "mult_two_numbers", ins={"a": In(int), "b": In(int)}, outs={DEFAULT_OUTPUT: Out(int)}
)


@op
def return_one():
    return 1


@op
def return_two():
    return 2


@op
def return_three():
    return 3


@op
def return_four():
    return 4


@job(resource_defs=common_resource_defs)
def add_job():
    add_two_numbers(return_one(), return_two())


@job(resource_defs=common_resource_defs)
def double_add_job():
    add_two_numbers.alias("add_two_numbers_1")(return_one(), return_two())
    add_two_numbers.alias("add_two_numbers_2")(return_three(), return_four())


@op(config_schema=Int)
def load_constant(context):
    return context.op_config


@job(resource_defs=common_resource_defs)
def notebook_dag_job():
    a = load_constant.alias("load_a")()
    b = load_constant.alias("load_b")()
    num, _ = add_two_numbers(a, b)
    mult_two_numbers(num, b)


error_notebook = test_nb_op("error_notebook", save_notebook_on_failure=True)


@job(resource_defs=common_resource_defs)
def error_job():
    error_notebook()


if DAGSTER_PANDAS_PRESENT and SKLEARN_PRESENT and MATPLOTLIB_PRESENT:
    clean_data = test_nb_op("clean_data", outs={DEFAULT_OUTPUT: Out(DataFrame)})

    # FIXME add an output to this
    tutorial_LR = test_nb_op("tutorial_LR", ins={"df": In(DataFrame)})

    tutorial_RF = test_nb_op("tutorial_RF", ins={"df": In(DataFrame)})

    @job(resource_defs=common_resource_defs)
    def tutorial_job():
        dfr, _ = clean_data()
        # FIXME get better names for these
        tutorial_LR(dfr)
        tutorial_RF(dfr)


@op(required_resource_keys={"list"})
def resource_op(context):
    context.resources.list.append("Hello, op!")
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


@job(
    resource_defs={
        "list": filepicklelist_resource,
        "output_notebook_io_manager": local_output_notebook_io_manager,
        "io_manager": fs_io_manager,
    }
)
def resource_job():
    hello_world_resource(resource_op())


@job(
    resource_defs={
        "list": filepicklelist_resource,
        "output_notebook_io_manager": local_output_notebook_io_manager,
        "io_manager": fs_io_manager,
    }
)
def resource_with_exception_job():
    hello_world_resource_with_exception(resource_op())


bad_kernel = test_nb_op("bad_kernel")


@job(resource_defs=common_resource_defs)
def bad_kernel_job():
    bad_kernel()


reimport = test_nb_op("reimport", ins={"l": In(List[int])}, outs={DEFAULT_OUTPUT: Out(int)})


@op
def lister():
    return [1, 2, 3]


@job(resource_defs=common_resource_defs)
def reimport_job():
    reimport(lister())


yield_3 = test_nb_op("yield_3", outs={DEFAULT_OUTPUT: Out(int)})


@job(resource_defs=common_resource_defs)
def yield_3_job():
    yield_3()


yield_obj = test_nb_op("yield_obj")


@job(resource_defs=common_resource_defs)
def yield_obj_job():
    yield_obj()


@job(resource_defs=common_resource_defs)
def retries_job():
    test_nb_op("raise_retry")()
    test_nb_op("yield_retry")()


@job(resource_defs=common_resource_defs)
def failure_job():
    test_nb_op("raise_failure")()
    test_nb_op("yield_failure")()


yield_something = test_nb_op(
    "yield_something", ins={"obj": In(str)}, outs={DEFAULT_OUTPUT: Out(str)}
)


@op
def fan_in(a, b):
    return f"{a} {b}"


@job(resource_defs=common_resource_defs)
def fan_in_notebook_job():
    val_a, _ = yield_something.alias("op_1")()
    val_b, _ = yield_something.alias("op_2")()
    fan_in(val_a, val_b)


@job(
    resource_defs={
        "output_notebook_io_manager": local_output_notebook_io_manager,
        "io_manager": mem_io_manager,
    }
)
def fan_in_notebook_job_in_mem():
    val_a, _ = yield_something.alias("op_1")()
    val_b, _ = yield_something.alias("op_2")()
    fan_in(val_a, val_b)


@graph
def outer():
    yield_something()


@job(resource_defs=common_resource_defs)
def graph_job():
    outer()


custom_io_mgr_key_op = dagstermill.factory.define_dagstermill_op(
    name="custom_io_mgr_op",
    notebook_path=nb_test_path("hello_world"),
    io_manager_key="my_custom_io_manager",
    output_notebook_name="my_notebook",
)


@job(resource_defs={"my_custom_io_manager": local_output_notebook_io_manager})
def custom_io_mgr_key_job():
    custom_io_mgr_key_op()


###################################################################################################
# Assets
###################################################################################################

hello_world_asset = dagstermill.define_dagstermill_asset(
    name="hello_world_asset", notebook_path=nb_test_path("hello_world")
)


hello_world_with_custom_tags_and_description_asset = dagstermill.define_dagstermill_asset(
    name="hello_world_custom_asset",
    notebook_path=nb_test_path("hello_world"),
    op_tags={"foo": "bar"},
    description="custom description",
)

hello_world_config_asset = dagstermill.define_dagstermill_asset(
    "hello_world_config_asset",
    notebook_path=nb_test_path("hello_world_config"),
    config_schema={"greeting": Field(String, is_required=False, default_value="hello")},
)


goodbye_config_asset = dagstermill.define_dagstermill_asset(
    name="goodbye_config_asset",
    notebook_path=nb_test_path("print_dagstermill_context_op_config"),
    config_schema={"farewell": Field(String, is_required=False, default_value="goodbye")},
)

hello_logging_asset = dagstermill.define_dagstermill_asset(
    name="hello_logging_asset", notebook_path=nb_test_path("hello_logging")
)

error_notebook_asset = dagstermill.define_dagstermill_asset(
    name="error_notebook_asset",
    notebook_path=nb_test_path("error_notebook"),
    save_notebook_on_failure=True,
)


@asset
def a():
    return 1


@asset
def b():
    return 2


add_two_number_asset = dagstermill.define_dagstermill_asset(
    name="add_two_numbers_asset",
    notebook_path=nb_test_path("add_two_numbers_no_yield"),
    ins={"a": AssetIn("a"), "b": AssetIn("b")},
)

hello_world_resource_asset = dagstermill.define_dagstermill_asset(
    "hello_world_resource_asset",
    notebook_path=nb_test_path("hello_world_resource"),
    required_resource_keys={"list"},
)

custom_io_mgr_key_asset = dagstermill.define_dagstermill_asset(
    name="custom_io_mgr_key",
    notebook_path=nb_test_path("hello_world"),
    io_manager_key="my_custom_io_manager",
)

yield_event_asset = dagstermill.define_dagstermill_asset(
    name="yield_event_asset", notebook_path=nb_test_path("yield_event")
)


# this is hacky. We need a ReconstructablePipeline to run dagstermill, and
# ReconstructablePipeline.for_module() find the jobs defined in this file. So we need to resolve all
# of the asset jobs outside of the repository function.
assets = with_resources(
    [
        hello_world_asset,
        hello_world_with_custom_tags_and_description_asset,
        hello_world_config_asset,
        goodbye_config_asset,
        hello_logging_asset,
        a,
        b,
        add_two_number_asset,
        hello_world_resource_asset,
        error_notebook_asset,
        yield_event_asset,
    ],
    resource_defs={
        "list": ResourceDefinition(lambda _: []),
        "output_notebook_io_manager": local_output_notebook_io_manager,
    },
)


def make_resolved_job(asset):
    return define_asset_job(
        name=f"{asset.key.to_user_string()}_job", selection=AssetSelection.assets(asset).upstream()
    ).resolve(assets, [])


hello_world_asset_job = make_resolved_job(hello_world_asset)
hello_world_with_custom_tags_and_description_asset_job = make_resolved_job(
    hello_world_with_custom_tags_and_description_asset
)
hello_world_config_asset_job = make_resolved_job(hello_world_config_asset)
goodbye_config_asset_job = make_resolved_job(goodbye_config_asset)
hello_logging_asset_job = make_resolved_job(hello_logging_asset)
add_two_number_asset_job = make_resolved_job(add_two_number_asset)
hello_world_resource_asset_job = make_resolved_job(hello_world_resource_asset)
error_notebook_asset_job = make_resolved_job(error_notebook_asset)
yield_event_asset_job = make_resolved_job(yield_event_asset)


@repository
def notebook_repo():
    repo = [
        bad_kernel_job,
        error_job,
        hello_world_job,
        hello_world_with_custom_tags_and_description_job,
        hello_world_config_job,
        hello_world_explicit_yield_job,
        hello_world_output_job,
        hello_world_with_output_notebook_job,
        hello_logging_job,
        resource_job,
        resource_with_exception_job,
        add_job,
        notebook_dag_job,
        reimport_job,
        yield_3_job,
        yield_obj_job,
        retries_job,
        failure_job,
        fan_in_notebook_job_in_mem,
        fan_in_notebook_job,
        hello_world_no_output_notebook_no_file_manager_job,
        *assets,
    ]
    if DAGSTER_PANDAS_PRESENT and SKLEARN_PRESENT and MATPLOTLIB_PRESENT:
        repo += [tutorial_job]

    return repo
