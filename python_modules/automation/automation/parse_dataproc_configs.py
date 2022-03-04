import os
import pprint
from collections import namedtuple

import requests

from .printer import IndentingBufferPrinter

SCALAR_TYPES = {
    "string": "String",
    "boolean": "Bool",
    "number": "Int",
    "enumeration": "String",
    "integer": "Int",
}


class List:
    def __init__(self, inner_type):
        self.inner_type = inner_type


class Enum:
    def __init__(self, name, enum_names, enum_descriptions):
        self.name = name
        self.enum_names = enum_names
        self.enum_descriptions = enum_descriptions

    def write(self, printer):
        printer.line(self.name.title() + " = Enum(")
        with printer.with_indent():
            printer.line("name='{}',".format(self.name.title()))
            printer.line("enum_values=[")
            with printer.with_indent():
                if self.enum_descriptions:
                    for name, value in zip(self.enum_names, self.enum_descriptions):
                        prefix = "EnumValue('{}', description='''".format(name)
                        printer.block(value + "'''),", initial_indent=prefix)
                else:
                    for name in self.enum_names:
                        printer.line("EnumValue('{}'),".format(name))

            printer.line("],")
        printer.line(")")


class Field:
    """Field represents a field type that we're going to write out as a dagster config field, once
    we've pre-processed all custom types
    """

    def __init__(self, fields, is_required, description):
        self.fields = fields
        self.is_required = is_required
        self.description = description

    def __repr__(self):
        return "Field(%s, %s, %s)" % (
            pprint.pformat(self.fields),
            str(self.is_required),
            self.description,
        )

    def _print_fields(self, printer):
        # Scalars
        if isinstance(self.fields, str):
            printer.append(self.fields)
        # Enums
        elif isinstance(self.fields, Enum):
            printer.append(self.fields.name)
        # Lists
        elif isinstance(self.fields, List):
            printer.append("[")
            self.fields.inner_type.write(printer, field_wrapped=False)
            printer.append("]")
        # Dicts
        else:
            printer.line("Shape(")
            with printer.with_indent():
                printer.line("fields={")
                with printer.with_indent():
                    for (k, v) in self.fields.items():
                        # We need to skip "output" fields which are API responses, not queries
                        if "Output only" in v.description:
                            continue

                        # This v is a terminal scalar type, print directly
                        if isinstance(v, str):
                            printer.line("'{}': {},".format(k, v))

                        # Recurse nested fields
                        else:
                            with printer.with_indent():
                                printer.append("'{}': ".format(k))
                            v.write(printer)
                            printer.append(",")
                printer.line("},")
            printer.line(")")

    def write(self, printer, field_wrapped=True):
        """Use field_wrapped=False for Lists that should not be wrapped in Field()"""
        if not field_wrapped:
            self._print_fields(printer)
            return printer.read()

        printer.append("Field(")
        printer.line("")
        with printer.with_indent():
            self._print_fields(printer)
            printer.append(",")
            # Print description
            if self.description:
                printer.block(
                    self.description.replace("'", "\\'") + "''',", initial_indent="description='''"
                )

            # Print is_required=True/False if defined; if not defined, default to True
            printer.line(
                "is_required=%s," % str(self.is_required if self.is_required is not None else True)
            )
        printer.line(")")
        return printer.read()


class ParsedConfig(namedtuple("_ParsedConfig", "name configs enums")):
    def __new__(cls, name, configs, enums):
        return super(ParsedConfig, cls).__new__(cls, name, configs, enums)

    def write_configs(self, base_path):
        configs_filename = "configs_%s.py" % self.name
        print("Writing", configs_filename)  # pylint: disable=print-call
        with open(os.path.join(base_path, configs_filename), "wb") as f:
            f.write(self.configs)

        enums_filename = "types_%s.py" % self.name
        with open(os.path.join(base_path, enums_filename), "wb") as f:
            f.write(self.enums)


class ConfigParser:
    def __init__(self, schemas):
        self.schemas = schemas

        # Stashing these in a global so that we can write out after we're done constructing configs
        self.all_enums = {}

    def extract_config(self, base_field, suffix):
        with IndentingBufferPrinter() as printer:
            printer.write_header()
            printer.line("from dagster import Bool, Field, Int, Permissive, Shape, String")
            printer.blank_line()

            # Optionally write enum includes
            if self.all_enums:
                printer.line(
                    "from .types_{} import {}".format(suffix, ", ".join(self.all_enums.keys()))
                )
                printer.blank_line()

            printer.line("def define_%s_config():" % suffix)
            with printer.with_indent():
                printer.append("return ")
                base_field.write(printer)

            return printer.read().strip().encode("utf-8")

    def extract_enums(self):
        if not self.all_enums:
            return

        with IndentingBufferPrinter() as printer:
            printer.write_header()
            printer.line("from dagster import Enum, EnumValue")
            printer.blank_line()
            for enum in self.all_enums:
                self.all_enums[enum].write(printer)
                printer.blank_line()
            return printer.read().strip().encode("utf-8")

    def parse_object(self, obj, name=None, depth=0, enum_descriptions=None):
        # This is a reference to another object that we should substitute by recursing
        if "$ref" in obj:
            name = obj["$ref"]
            return self.parse_object(self.schemas.get(name), name, depth + 1)

        # Print type tree
        prefix = "|" + ("-" * 4 * depth) + " " if depth > 0 else ""
        print(prefix + (name or obj.get("type")))  # pylint: disable=print-call

        # Switch on object type
        obj_type = obj.get("type")

        # Handle enums
        if "enum" in obj:
            # I think this is a bug in the API JSON spec where enum descriptions are a level higher
            # than they should be for type "Component" and the name isn't there
            if name is None:
                name = "Component"

            enum = Enum(name, obj["enum"], enum_descriptions or obj.get("enumDescriptions"))
            self.all_enums[name] = enum
            fields = enum

        # Handle dicts / objects
        elif obj_type == "object":
            # This is a generic k:v map
            if "additionalProperties" in obj:
                fields = "Permissive()"
            else:
                fields = {
                    k: self.parse_object(v, k, depth + 1) for k, v in obj["properties"].items()
                }

        # Handle arrays
        elif obj_type == "array":
            fields = List(
                self.parse_object(
                    obj.get("items"), None, depth + 1, enum_descriptions=obj.get("enumDescriptions")
                )
            )

        # Scalars
        elif obj_type in SCALAR_TYPES:
            fields = SCALAR_TYPES.get(obj_type)

        # Should never get here
        else:
            raise Exception("unknown type: ", obj)

        return Field(fields, is_required=None, description=obj.get("description"))

    def extract_schema_for_object(self, object_name, name):
        # Reset enums for this object
        self.all_enums = {}

        obj = self.parse_object(self.schemas.get(object_name), object_name)
        return ParsedConfig(
            name=name, configs=self.extract_config(obj, name), enums=self.extract_enums()
        )


def main():
    api_url = "https://www.googleapis.com/discovery/v1/apis/dataproc/v1/rest"
    base_path = "../libraries/dagster-gcp/dagster_gcp/dataproc/"
    json_schema = requests.get(api_url).json().get("schemas")

    c = ConfigParser(json_schema)
    parsed = c.extract_schema_for_object("Job", "dataproc_job")
    parsed.write_configs(base_path)

    parsed = c.extract_schema_for_object("ClusterConfig", "dataproc_cluster")
    parsed.write_configs(base_path)


if __name__ == "__main__":
    main()
