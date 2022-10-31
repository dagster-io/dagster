import importlib.util
import json
import os
import re
import subprocess
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Sequence, Union

import click
import yaml

import dagster._check as check
from dagster._utils import file_relative_path, mkdir_p


def _remove_invalid_chars(name: str) -> str:
    return "".join([(x if x.isalnum() else "_") for x in name])


# Any keywords we should avoid using as class names
KEYWORDS = ["None", "Any", "Union", "List", "Dict", "Optional", "T"]


def _to_class_name(name: str) -> str:
    class_name = "".join([_remove_invalid_chars(x).capitalize() for x in re.split("\W+", name)])
    if class_name in KEYWORDS:
        class_name += "_"
    return class_name


class SchemaType(ABC):
    @abstractmethod
    def get_check(self, name: str, scope: Optional[str] = None):
        pass

    @abstractmethod
    def annotation(self, scope: Optional[str] = None, quote: bool = False):
        pass

    @property
    def const_value(self):
        return None


TYPE_MAPPING = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
}


CHECK_MAPPING = {
    "str": "check.str_param({}, '{}')",
    "int": "check.int_param({}, '{}')",
    "float": "check.float_param({}, '{}')",
    "bool": "check.bool_param({}, '{}')",
}


class RawType(SchemaType):
    def __init__(self, schema_type_str: str, const_value: Optional[Any] = None):
        if schema_type_str in TYPE_MAPPING:
            self.type_str = TYPE_MAPPING[schema_type_str]
        else:
            self.type_str = schema_type_str
        self._const_value = const_value

    def __str__(self):
        return self.type_str

    @property
    def const_value(self):
        return self._const_value

    def annotation(self, scope: Optional[str] = None, quote: bool = False):
        if self.type_str in CHECK_MAPPING:
            return self.type_str
        scope = f"{scope}." if scope else ""

        if quote:
            return f'"{scope}{self.type_str}"'
        return f"{scope}{self.type_str}"

    def get_check(self, name: str, scope: Optional[str] = None):
        if self.type_str in CHECK_MAPPING:
            return CHECK_MAPPING[self.type_str].format(name, name)
        scope = f"{scope}." if scope else ""
        return "check.inst_param({}, '{}', {}{})".format(name, name, scope, self.type_str)


class OptType(SchemaType):
    def __init__(self, inner: SchemaType):
        self.inner = inner

    def __str__(self):
        return f"Optional[{self.inner}]"

    def annotation(self, scope: Optional[str] = None, quote: bool = False):
        return f"Optional[{self.inner.annotation(scope, quote)}] = None"

    def get_check(self, name: str, scope: Optional[str] = None):
        inner_check = self.inner.get_check(name, scope)
        return ".opt_".join(inner_check.split(".", 1))


class ListType(SchemaType):
    def __init__(self, inner: SchemaType):
        self.inner = inner

    def __str__(self):
        return f"List[{self.inner}]"

    def annotation(self, scope: Optional[str] = None, quote: bool = False):
        return f"List[{self.inner.annotation(scope, quote)}]"

    def get_check(self, name: str, scope: Optional[str] = None):
        return "check.list_param({}, '{}', {})".format(name, name, str(self.inner))


class UnionType(SchemaType):
    def __init__(self, inner: Sequence[SchemaType]):
        self.inner = inner

    def __str__(self):
        return f"Union[{', '.join([str(x) for x in self.inner])}]"

    def annotation(self, scope: Optional[str] = None, quote: bool = False):
        return f"Union[{', '.join([x.annotation(scope, quote) for x in self.inner])}]"

    def get_check(self, name: str, scope: Optional[str] = None):
        scope = f"{scope}." if scope else ""
        return "check.inst_param({}, '{}', {})".format(
            name, name, "({})".format(", ".join([scope + str(x) for x in self.inner]))
        )


def _union_or_singular(inner: List[SchemaType]) -> SchemaType:
    if len(inner) == 1:
        return inner[0]
    return UnionType(inner)


def get_class_definitions(name: str, schema: dict) -> Dict[str, Dict[str, SchemaType]]:
    class_definitions = {}

    fields = {}

    required_fields = set(schema.get("required", []))
    for field_name, field in schema["properties"].items():
        if field_name == "option_title":
            continue

        field_name = _remove_invalid_chars(field_name)

        if "oneOf" in field:
            union_type = []
            for sub_field in field["oneOf"]:
                title = sub_field.get("properties", {}).get("option_title", {}).get("const")
                if not title:
                    title = sub_field.get("title")
                title = _to_class_name(title)
                class_definitions = {
                    **class_definitions,
                    **get_class_definitions(title, sub_field),
                }
                union_type.append(RawType(title))
            fields[field_name] = _union_or_singular(union_type)
        else:
            field_type = field.get("type", "string")
            if field_type == "object":
                title = _to_class_name(field.get("title") or field.get("description"))
                class_definitions = {
                    **class_definitions,
                    **get_class_definitions(title, field),
                }
                fields[field_name] = RawType(title)
            elif type(field_type) == list:
                fields[field_name] = _union_or_singular(
                    [RawType(sub_type) for sub_type in field_type if sub_type != "null"]
                )
                if "null" in field_type:
                    fields[field_name] = OptType(fields[field_name])
            else:
                if field_type == "array":
                    array_type = field.get("items", {}).get("type") or field.get("item") or "string"
                    check.not_none(array_type)
                    fields[field_name] = ListType(RawType(array_type))
                else:
                    fields[field_name] = RawType(field_type, const_value=field.get("const"))
                if field_name not in required_fields:
                    fields[field_name] = OptType(fields[field_name])

    class_definitions[name] = fields
    return class_definitions


CLASS_TEMPLATE = """
class {cls_name}:
    def __init__(self, {fields_in}):
{self_fields}
"""


SOURCE_TEMPLATE = '''
class {cls_name}(GeneratedAirbyteSource): {nested_defs}
    def __init__(self, name: str, {fields_in}):
        """
        Airbyte Source for {human_readable_name}

        Documentation can be found at {docs_url}
        """
{self_fields}
        super().__init__("{human_readable_name}", name)
'''

DESTINATION_TEMPLATE = '''
class {cls_name}(GeneratedAirbyteDestination): {nested_defs}
    def __init__(self, name: str, {fields_in}):
        """
        Airbyte Destination for {human_readable_name}

        Documentation can be found at {docs_url}
        """
{self_fields}
        super().__init__("{human_readable_name}", name)
'''


def create_nested_class_definition(
    base_cls_name: str,
    cls_name: str,
    cls_def: Dict[str, SchemaType],
):
    nested_defs = ""
    fields_in = ", ".join(
        [
            f"{field_name}: {field_type.annotation(scope=base_cls_name, quote=True)}"
            for field_name, field_type in sorted(
                cls_def.items(), key=lambda x: isinstance(x[1], OptType)
            )
            if field_type.const_value is None
        ]
    )

    self_fields = "\n".join(
        [
            f'        self.{field_name} = "{field_type.const_value}"'
            for field_name, field_type in cls_def.items()
            if field_type.const_value is not None
        ]
        + [
            f"        self.{field_name} = {field_type.get_check(field_name, scope=base_cls_name)}"
            for field_name, field_type in cls_def.items()
            if field_type.const_value is None
        ]
    )
    return CLASS_TEMPLATE.format(
        cls_name=cls_name,
        fields_in=fields_in,
        self_fields=self_fields,
        nested_defs=nested_defs,
    )


def create_connector_class_definition(
    connector_name_human_readable: str,
    cls_name: str,
    cls_def: Dict[str, SchemaType],
    nested: Optional[List[str]],
    is_source: bool,
    docs_url: str,
):
    nested_defs = ""
    if nested:
        nested_defs = "\n".join(
            ["\n".join([f"    {x}" for x in nested_def.split("\n")]) for nested_def in nested]
        )
    fields_in = ", ".join(
        [
            f"{field_name}: {field_type} = None"
            if isinstance(field_type, OptType)
            else f"{field_name}: {field_type}"
            for field_name, field_type in sorted(
                cls_def.items(), key=lambda x: isinstance(x[1], OptType)
            )
            if field_type.const_value is None
        ]
    )

    self_fields = "\n".join(
        [
            f'        self.{field_name} = "{field_type.const_value}"'
            for field_name, field_type in cls_def.items()
            if field_type.const_value is not None
        ]
        + [
            f"        self.{field_name} = {field_type.get_check(field_name, scope = cls_name)}"
            for field_name, field_type in cls_def.items()
            if field_type.const_value is None
        ]
    )
    return (SOURCE_TEMPLATE if is_source else DESTINATION_TEMPLATE).format(
        cls_name=cls_name,
        fields_in=fields_in,
        self_fields=self_fields,
        nested_defs=nested_defs,
        human_readable_name=connector_name_human_readable,
        docs_url=docs_url,
    )


class GithubSource:
    class ServiceAccount:
        def __init__(self, username: str, secret: str):
            self.username = check.str_param(username, "username")
            self.secret = check.str_param(secret, "secret")

    class ProjectSecret:
        def __init__(self, api_secret: str):
            self.api_secret = check.str_param(api_secret, "api_secret")

    def __init__(
        self,
        credentials: Optional[Union[ServiceAccount, ProjectSecret]],
        project_id: Optional[int],
        attribution_window: Optional[int],
        project_timezone: Optional[str],
        select_properties_by_default: Optional[bool],
        start_date: Optional[str],
        end_date: Optional[str],
        region: Optional[str],
        date_window_size: Optional[int],
    ):
        self.credentials = check.opt_inst_param(
            credentials, "credentials", (GithubSource.ServiceAccount, GithubSource.ProjectSecret)
        )
        self.project_id = check.opt_int_param(project_id, "project_id")
        self.attribution_window = check.opt_int_param(attribution_window, "attribution_window")
        self.project_timezone = check.opt_str_param(project_timezone, "project_timezone")
        self.select_properties_by_default = check.opt_bool_param(
            select_properties_by_default, "select_properties_by_default"
        )
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.end_date = check.opt_str_param(end_date, "end_date")
        self.region = check.opt_str_param(region, "region")
        self.date_window_size = check.opt_int_param(date_window_size, "date_window_size")


def load_from_spec_file(
    connector_name_human_readable: str, connector_name: str, filepath: str, is_source: bool
):
    """
    Loads a connector spec file and generates a python class definition for it
    """

    with open(filepath, encoding="utf8") as f:
        if filepath.endswith(".json"):
            schema = json.loads(f.read())
        else:
            schema = yaml.safe_load(f.read())

    cls_defs = get_class_definitions(connector_name, schema["connectionSpecification"])
    defs = []
    for cls_name, cls_def in cls_defs.items():
        if cls_name != connector_name:
            defs.append(create_nested_class_definition(connector_name, cls_name, cls_def))

    return create_connector_class_definition(
        connector_name_human_readable,
        connector_name,
        cls_defs[connector_name],
        defs,
        is_source,
        schema["documentationUrl"],
    )


SOURCE_OUT_FILE = "/Users/ben/Documents/repos/dagster/python_modules/libraries/dagster-airbyte/dagster_airbyte/managed/generated/sources.py"
DEST_OUT_FILE = "/Users/ben/Documents/repos/dagster/python_modules/libraries/dagster-airbyte/dagster_airbyte/managed/generated/destinations.py"


AIRBYTE_REPO_URL = "https://github.com/airbytehq/airbyte.git"


@contextmanager
def airbyte_repo_path(airbyte_repo_root: Optional[str], tag: str):
    if airbyte_repo_root:
        os.chdir(airbyte_repo_root)
        subprocess.call(["git", "checkout", f"origin/{tag}"])

        yield airbyte_repo_root
    else:
        build_dir = os.path.abspath(file_relative_path(__file__, ".build"))
        mkdir_p(build_dir)
        os.chdir(build_dir)
        subprocess.call(["git", "clone", "--depth", "1", "--branch", "master", AIRBYTE_REPO_URL])
        os.chdir("./airbyte")
        subprocess.call(["git", "fetch", "--all", "--tags"])
        subprocess.call(["git", "checkout", "-b" f"tags/{tag}", f"tags/{tag}"])

        yield os.path.join(str(build_dir), "airbyte")


EXPECTED_FAILURES = [
    # "Dv 360",
    "E2e Test",
]


@click.command()
@click.option(
    "--airbyte-repo-root",
    "-a",
    default=None,
    help="Path to a cloned copy of Airbyte, defaults to cloning a temp copy",
)
@click.option(
    "--airbyte-tag",
    "-t",
    default="v0.40.17",
    help="Airbyte tag to use, defaults to v0.40.17",
)
def gen_airbyte_classes(airbyte_repo_root, airbyte_tag):
    with airbyte_repo_path(airbyte_repo_root, airbyte_tag) as airbyte_dir:
        connectors_root = os.path.join(airbyte_dir, "airbyte-integrations/connectors")

        for (title, prefix, out_file, imp, is_source) in [
            ("Source", "source-", SOURCE_OUT_FILE, "GeneratedAirbyteSource", True),
            ("Destination", "destination-", DEST_OUT_FILE, "GeneratedAirbyteDestination", False),
        ]:
            successes = 0
            failures = []

            click.secho(f"\n\nGenerating Airbyte {title} Classes...\n\n\n", fg="green")

            out = f"""from typing import Any, List, Optional, Union

from dagster_airbyte.managed.types import {imp}

import dagster._check as check



"""

            for connector_package in os.listdir(connectors_root):
                connector_name_parts = [x.capitalize() for x in connector_package.split("-")]
                connector_name_human_readable = " ".join(connector_name_parts[1:])
                connector_name = "".join(connector_name_parts[1:] + connector_name_parts[:1])

                if connector_package.startswith(prefix):
                    for root, _dirs, files in os.walk(
                        os.path.join(connectors_root, connector_package)
                    ):
                        for file in files:
                            if file == "spec.json" or file == "spec.yml" or file == "spec.yaml":

                                # First, attempt to load the spec file and generate
                                # the class definition
                                new_out = out
                                try:
                                    new_out += load_from_spec_file(
                                        connector_name_human_readable,
                                        connector_name,
                                        os.path.join(root, file),
                                        is_source,
                                    )
                                except Exception as e:
                                    failures.append((connector_name_human_readable, e))
                                    continue

                                with open(out_file, "w", encoding="utf8") as f:
                                    f.write(new_out)

                                # Next, attempt to load the spec file and
                                # abort if it fails, recording the failure
                                try:
                                    spec = importlib.util.spec_from_file_location(
                                        "module.name", out_file
                                    )
                                    foo = importlib.util.module_from_spec(spec)
                                    sys.modules["module.name"] = foo
                                    spec.loader.exec_module(foo)

                                    out = new_out
                                    successes += 1
                                except Exception as e:
                                    failures.append((connector_name_human_readable, e))
                                    continue

                print("\033[1A\033[K\033[1A\033[K\033[1A\033[K")
                click.secho(f"{successes} successes", fg="green")
                click.secho(f"{len(failures)} failures", fg="red")

            for failure in failures:
                click.secho(f"{failure[0]}: {failure[1]}", fg="red")

                if failure[0] not in EXPECTED_FAILURES:
                    raise failure[1]

            subprocess.call(["black", out_file])


if __name__ == "__main__":
    gen_airbyte_classes()
