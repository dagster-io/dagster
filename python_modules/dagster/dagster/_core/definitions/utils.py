import keyword
import os
import re
import warnings
from glob import glob
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

import yaml

import dagster._check as check
import dagster._seven as seven
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster._core.storage.tags import check_reserved_tags
from dagster._core.utils import is_valid_email
from dagster._utils.yaml_utils import merge_yaml_strings, merge_yamls

DEFAULT_OUTPUT = "result"
DEFAULT_GROUP_NAME = "default"  # asset group_name used when none is provided
DEFAULT_IO_MANAGER_KEY = "io_manager"

DISALLOWED_NAMES = set(
    [
        "context",
        "conf",
        "config",
        "meta",
        "arg_dict",
        "dict",
        "input_arg_dict",
        "output_arg_dict",
        "int",
        "str",
        "float",
        "bool",
        "input",
        "output",
        "type",
    ]
    + list(keyword.kwlist)  # just disallow all python keywords
)

INVALID_NAME_CHARS = r"[^A-Za-z0-9_]"
VALID_NAME_REGEX_STR = r"^[A-Za-z0-9_]+$"
VALID_NAME_REGEX = re.compile(VALID_NAME_REGEX_STR)

INVALID_TITLE_CHARACTERS_REGEX_STR = r"[\%\*\"]"
INVALID_TITLE_CHARACTERS_REGEX = re.compile(INVALID_TITLE_CHARACTERS_REGEX_STR)
MAX_TITLE_LENGTH = 100

if TYPE_CHECKING:
    from dagster._core.definitions.asset_key import AssetKey


class NoValueSentinel:
    """Sentinel value to distinguish unset from None."""


def has_valid_name_chars(name: str) -> bool:
    return bool(VALID_NAME_REGEX.match(name))


def check_valid_name(name: str, allow_list: Optional[List[str]] = None) -> str:
    check.str_param(name, "name")

    if allow_list and name in allow_list:
        return name

    if name in DISALLOWED_NAMES:
        raise DagsterInvalidDefinitionError(
            f'"{name}" is not a valid name in Dagster. It conflicts with a Dagster or python'
            " reserved keyword."
        )

    check_valid_chars(name)

    check.invariant(is_valid_name(name))
    return name


def check_valid_chars(name: str):
    if not has_valid_name_chars(name):
        raise DagsterInvalidDefinitionError(
            f'"{name}" is not a valid name in Dagster. Names must be in regex'
            f" {VALID_NAME_REGEX_STR}."
        )


def is_valid_name(name: str) -> bool:
    check.str_param(name, "name")

    return name not in DISALLOWED_NAMES and has_valid_name_chars(name)


def is_valid_title_and_reason(title: Optional[str]) -> Tuple[bool, Optional[str]]:
    check.opt_str_param(title, "title")

    if title is None:
        return True, None

    if len(title) > MAX_TITLE_LENGTH:
        return (
            False,
            f'"{title}" ({len(title)} characters) is not a valid title in Dagster. Titles must not be longer than {MAX_TITLE_LENGTH}.',
        )

    if not is_valid_title_chars(title):
        return (
            False,
            f'"{title}" is not a valid title in Dagster. Titles must not contain regex {INVALID_TITLE_CHARACTERS_REGEX_STR}.',
        )

    return True, None


def check_valid_title(title: Optional[str]) -> Optional[str]:
    """A title is distinguished from a name in that the title is a descriptive string meant for display in the UI.
    It is not used as an identifier for an object.
    """
    is_valid, reason = is_valid_title_and_reason(title)
    if not is_valid:
        raise DagsterInvariantViolationError(reason)

    return title


def is_valid_title(title: Optional[str]) -> bool:
    return is_valid_title_and_reason(title)[0]


def is_valid_title_chars(title: str):
    return not bool(INVALID_TITLE_CHARACTERS_REGEX.search(title))


def _kv_str(key: object, value: object) -> str:
    return f'{key}="{value!r}"'


def struct_to_string(name: str, **kwargs: object) -> str:
    # Sort the kwargs to ensure consistent representations across Python versions
    props_str = ", ".join([_kv_str(key, value) for key, value in sorted(kwargs.items())])
    return f"{name}({props_str})"


class NormalizedTags(NamedTuple):
    tags: Mapping[str, str]

    def with_normalized_tags(self, normalized_tags: "NormalizedTags") -> "NormalizedTags":
        return NormalizedTags({**self.tags, **normalized_tags.tags})


def normalize_tags(
    tags: Union[NormalizedTags, Optional[Mapping[str, Any]]],
    allow_reserved_tags: bool = True,
    warn_on_deprecated_tags: bool = True,
    warning_stacklevel: int = 4,
) -> NormalizedTags:
    """Normalizes JSON-object tags into string tags and warns on deprecated tags.

    New tags properties should _not_ use this function, because it doesn't hard error on tags that
    are no longer supported.
    """
    if isinstance(tags, NormalizedTags):
        return tags

    valid_tags: Dict[str, str] = {}
    invalid_tag_keys = []
    for key, value in check.opt_mapping_param(tags, "tags", key_type=str).items():
        if not isinstance(value, str):
            valid = False
            err_reason = f'Could not JSON encode value "{value}"'
            str_val = None
            try:
                str_val = seven.json.dumps(value)
                err_reason = f'JSON encoding "{str_val}" of value "{value}" is not equivalent to original value'

                valid = seven.json.loads(str_val) == value
            except Exception:
                pass

            if not valid:
                raise DagsterInvalidDefinitionError(
                    f'Invalid value for tag "{key}", {err_reason}. Tag values must be strings '
                    "or meet the constraint that json.loads(json.dumps(value)) == value."
                )

            valid_tags[key] = str_val  # type: ignore  # (possible none)
        else:
            valid_tags[key] = value

        if not is_valid_definition_tag_key(key):
            invalid_tag_keys.append(key)

    if invalid_tag_keys:
        invalid_tag_keys_sample = invalid_tag_keys[: min(5, len(invalid_tag_keys))]
        if warn_on_deprecated_tags:
            warnings.warn(
                f"Non-compliant tag keys like {invalid_tag_keys_sample} are deprecated. {VALID_DEFINITION_TAG_KEY_EXPLANATION}",
                category=DeprecationWarning,
                stacklevel=warning_stacklevel,
            )

    if not allow_reserved_tags:
        check_reserved_tags(valid_tags)

    return NormalizedTags(valid_tags)


# Inspired by allowed Kubernetes labels:
# https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set
VALID_DEFINITION_TAG_KEY_REGEX_STR = r"^([A-Za-z0-9_.-]{1,63}/)?[A-Za-z0-9_.-]{1,63}$"
VALID_DEFINITION_TAG_KEY_REGEX = re.compile(VALID_DEFINITION_TAG_KEY_REGEX_STR)
VALID_DEFINITION_TAG_KEY_EXPLANATION = (
    "Allowed characters: alpha-numeric, '_', '-', '.'. "
    "Tag keys can also contain a namespace section, separated by a '/'. Each section "
    "must have <= 63 characters."
)

VALID_DEFINITION_TAG_VALUE_REGEX_STR = r"^[A-Za-z0-9_.-]{0,63}$"
VALID_DEFINITION_TAG_VALUE_REGEX = re.compile(VALID_DEFINITION_TAG_VALUE_REGEX_STR)


def is_valid_definition_tag_key(key: str) -> bool:
    return bool(VALID_DEFINITION_TAG_KEY_REGEX.match(key))


def is_valid_definition_tag_value(key: str) -> bool:
    return bool(VALID_DEFINITION_TAG_VALUE_REGEX.match(key))


def validate_tags_strict(tags: Optional[Mapping[str, str]]) -> Optional[Mapping[str, str]]:
    if tags is None:
        return tags

    for key, value in tags.items():
        validate_tag_strict(key, value)

    return tags


def validate_tag_strict(key: str, value: str) -> None:
    if not isinstance(key, str):
        raise DagsterInvalidDefinitionError("Tag keys must be strings")

    if not isinstance(value, str):
        raise DagsterInvalidDefinitionError("Tag values must be strings")

    if not is_valid_definition_tag_key(key):
        raise DagsterInvalidDefinitionError(
            f"Invalid tag key: {key}. {VALID_DEFINITION_TAG_KEY_EXPLANATION}"
        )

    if not is_valid_definition_tag_value(value):
        raise DagsterInvalidDefinitionError(
            f"Invalid tag value: {value}, for key: {key}. Allowed characters: alpha-numeric, '_', '-', '.'. "
            "Must have <= 63 characters."
        )


def validate_asset_owner(owner: str, key: "AssetKey") -> None:
    if not is_valid_email(owner) and not (owner.startswith("team:") and len(owner) > 5):
        raise DagsterInvalidDefinitionError(
            f"Invalid owner '{owner}' for asset '{key}'. Owner must be an email address or a team "
            "name prefixed with 'team:'."
        )


def normalize_group_name(group_name: Optional[str]) -> str:
    """Ensures a string name is valid and returns a default if no name provided."""
    if group_name:
        check_valid_chars(group_name)
        return group_name
    elif group_name == "":
        raise DagsterInvalidDefinitionError(
            "Empty asset group name was provided, which is not permitted."
            "Set group_name=None to use the default group_name or set non-empty string"
        )
    return DEFAULT_GROUP_NAME


def config_from_files(config_files: Sequence[str]) -> Mapping[str, Any]:
    """Constructs run config from YAML files.

    Args:
        config_files (List[str]): List of paths or glob patterns for yaml files
            to load and parse as the run config.

    Returns:
        Dict[str, Any]: A run config dictionary constructed from provided YAML files.

    Raises:
        FileNotFoundError: When a config file produces no results
        DagsterInvariantViolationError: When one of the YAML files is invalid and has a parse
            error.
    """
    config_files = check.opt_sequence_param(config_files, "config_files")

    filenames = []
    for file_glob in config_files or []:
        globbed_files = glob(file_glob)
        if not globbed_files:
            raise DagsterInvariantViolationError(
                f'File or glob pattern "{file_glob}" for "config_files" produced no results.'
            )

        filenames += [os.path.realpath(globbed_file) for globbed_file in globbed_files]

    try:
        run_config = merge_yamls(filenames)
    except yaml.YAMLError as err:
        raise DagsterInvariantViolationError(
            f"Encountered error attempting to parse yaml. Parsing files {filenames} "
            f"loaded by file/patterns {config_files}."
        ) from err

    return check.is_dict(cast(Dict[str, object], run_config), key_type=str)


def config_from_yaml_strings(yaml_strings: Sequence[str]) -> Mapping[str, Any]:
    """Static constructor for run configs from YAML strings.

    Args:
        yaml_strings (List[str]): List of yaml strings to parse as the run config.

    Returns:
        Dict[Str, Any]: A run config dictionary constructed from the provided yaml strings

    Raises:
        DagsterInvariantViolationError: When one of the YAML documents is invalid and has a
            parse error.
    """
    yaml_strings = check.sequence_param(yaml_strings, "yaml_strings", of_type=str)

    try:
        run_config = merge_yaml_strings(yaml_strings)
    except yaml.YAMLError as err:
        raise DagsterInvariantViolationError(
            f"Encountered error attempting to parse yaml. Parsing YAMLs {yaml_strings} "
        ) from err

    return check.is_dict(cast(Dict[str, object], run_config), key_type=str)


def config_from_pkg_resources(pkg_resource_defs: Sequence[Tuple[str, str]]) -> Mapping[str, Any]:
    """Load a run config from a package resource, using :py:func:`pkg_resources.resource_string`.

    Example:
        .. code-block:: python

            config_from_pkg_resources(
                pkg_resource_defs=[
                    ('dagster_examples.airline_demo.environments', 'local_base.yaml'),
                    ('dagster_examples.airline_demo.environments', 'local_warehouse.yaml'),
                ],
            )


    Args:
        pkg_resource_defs (List[(str, str)]): List of pkg_resource modules/files to
            load as the run config.

    Returns:
        Dict[Str, Any]: A run config dictionary constructed from the provided yaml strings

    Raises:
        DagsterInvariantViolationError: When one of the YAML documents is invalid and has a
            parse error.
    """
    import pkg_resources  # expensive, import only on use

    pkg_resource_defs = check.sequence_param(pkg_resource_defs, "pkg_resource_defs", of_type=tuple)

    try:
        yaml_strings = [
            pkg_resources.resource_string(*pkg_resource_def).decode("utf-8")
            for pkg_resource_def in pkg_resource_defs
        ]
    except (ModuleNotFoundError, FileNotFoundError, UnicodeDecodeError) as err:
        raise DagsterInvariantViolationError(
            "Encountered error attempting to parse yaml. Loading YAMLs from "
            f"package resources {pkg_resource_defs}."
        ) from err

    return config_from_yaml_strings(yaml_strings=yaml_strings)
