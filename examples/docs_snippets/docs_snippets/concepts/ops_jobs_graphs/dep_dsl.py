from dagster._utils.yaml_utils import load_yaml_from_path

# isort: split

# start
import os

from dagster import DependencyDefinition, GraphDefinition, NodeInvocation, op


@op
def add_one(num: int) -> int:
    return num + 1


@op
def add_two(num: int) -> int:
    return num + 2


@op
def subtract(left: int, right: int) -> int:
    return left + right


def construct_graph_with_yaml(yaml_file, op_defs) -> GraphDefinition:
    yaml_data = load_yaml_from_path(yaml_file)

    deps = {}

    for op_yaml_data in yaml_data["ops"]:
        def_name = op_yaml_data["def"]
        alias = op_yaml_data.get("alias", def_name)
        op_deps_entry = {}
        for input_name, input_data in op_yaml_data.get("deps", {}).items():
            op_deps_entry[input_name] = DependencyDefinition(
                solid=input_data["op"], output=input_data.get("output", "result")
            )
        deps[NodeInvocation(name=def_name, alias=alias)] = op_deps_entry

    return GraphDefinition(
        name=yaml_data["name"],
        description=yaml_data.get("description"),
        node_defs=op_defs,
        dependencies=deps,
    )


def define_dep_dsl_graph() -> GraphDefinition:
    path = os.path.join(os.path.dirname(__file__), "my_graph.yaml")
    return construct_graph_with_yaml(path, [add_one, add_two, subtract])
