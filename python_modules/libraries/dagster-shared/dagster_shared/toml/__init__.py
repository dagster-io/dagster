import contextlib
import re
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional, TypeVar, Union, overload

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    import tomlkit

TomlPath: TypeAlias = tuple[Union[str, int], ...]
TomlDoc: TypeAlias = Union["tomlkit.TOMLDocument", dict[str, Any]]
T = TypeVar("T")


def load_toml_as_dict(path: Path) -> dict[str, Any]:
    import tomlkit

    return tomlkit.parse(path.read_text()).unwrap()


def get_toml_node(
    doc: TomlDoc,
    path: TomlPath,
    expected_type: Union[type[T], tuple[type[T], ...]],
) -> T:
    """Given a tomlkit-parsed document/table (`doc`),retrieve the nested value at `path` and ensure
    it is of type `expected_type`. Returns the value if so, or raises a KeyError / TypeError if not.
    """
    value = _gather_toml_nodes(doc, path)[-1]
    if not isinstance(value, expected_type):
        expected_types = expected_type if isinstance(expected_type, tuple) else (expected_type,)
        type_str = " or ".join(t.__name__ for t in expected_types)
        raise TypeError(
            f"Expected '{toml_path_to_str(path)}' to be {type_str}, "
            f"but got {type(value).__name__} instead."
        )
    return value


def has_toml_node(doc: TomlDoc, path: TomlPath) -> bool:
    """Given a tomlkit-parsed document/table (`doc`), return whether a value is defined at `path`."""
    result = _gather_toml_nodes(doc, path, error_on_missing=False)
    return False if result is None else True


def delete_toml_node(doc: TomlDoc, path: TomlPath) -> None:
    """Given a tomlkit-parsed document/table (`doc`), delete the nested value at `path`. Raises
    an error if the leading keys do not already lead to a TOML container node.
    """
    import tomlkit

    nodes = _gather_toml_nodes(doc, path)
    container = nodes[-2] if len(nodes) > 1 else doc
    key_or_index = path[-1]
    if isinstance(container, dict):
        assert isinstance(key_or_index, str)  # We already know this from _traverse_toml_path
        del container[key_or_index]
    elif isinstance(container, tomlkit.TOMLDocument):
        assert isinstance(key_or_index, str)  # We already know this from _traverse_toml_path
        container.remove(key_or_index)
    elif isinstance(container, list):
        assert isinstance(key_or_index, int)  # We already know this from _traverse_toml_path
        container.pop(key_or_index)
    else:
        raise Exception("Unreachable.")


def set_toml_node(doc: TomlDoc, path: TomlPath, value: object) -> None:
    """Given a tomlkit-parsed document/table (`doc`),set a nested value at `path` to `value`. Raises
    an error if the leading keys do not already lead to a TOML container node.
    """
    container = _gather_toml_nodes(doc, path[:-1])[-1] if len(path) > 1 else doc
    key_or_index = path[-1]  # type: ignore  # pyright bug
    if isinstance(container, dict):
        if not isinstance(key_or_index, str):
            raise TypeError(f"Expected key to be a string, but got {type(key_or_index).__name__}")
        container[key_or_index] = value
    elif isinstance(container, list):
        if not isinstance(key_or_index, int):
            raise TypeError(f"Expected key to be an integer, but got {type(key_or_index).__name__}")
        container[key_or_index] = value
    else:
        raise Exception("Unreachable.")


@overload
def _gather_toml_nodes(
    doc: TomlDoc, path: TomlPath, error_on_missing: Literal[True] = ...
) -> list[Any]: ...


@overload
def _gather_toml_nodes(
    doc: TomlDoc, path: TomlPath, error_on_missing: Literal[False] = ...
) -> Optional[list[Any]]: ...


def _gather_toml_nodes(
    doc: TomlDoc, path: TomlPath, error_on_missing: bool = True
) -> Optional[list[Any]]:
    nodes: list[Any] = []
    current: Any = doc
    for key in path:
        if isinstance(key, str):
            if not isinstance(current, dict) or key not in current:
                if error_on_missing:
                    raise KeyError(f"Key '{key}' not found in path: {toml_path_to_str(path)}")
                return None
            current = current[key]
        elif isinstance(key, int):
            if not isinstance(current, list) or key < 0 or key >= len(current):
                if error_on_missing:
                    raise KeyError(f"Index '{key}' not found in path: {toml_path_to_str(path)}")
                return None
            current = current[key]
        else:
            raise TypeError(f"Expected key to be a string or integer, but got {type(key)}")
        nodes.append(current)

    return nodes


def toml_path_to_str(path: TomlPath) -> str:
    if len(path) == 0:
        return ""
    first = path[0]
    if not isinstance(first, str):
        raise TypeError(f"Expected first element of path to be a string, but got {type(first)}")
    elif len(path) == 1:
        return first
    else:
        str_path = first
        for item in path[1:]:
            if isinstance(item, int):
                str_path += f"[{item}]"
            elif isinstance(item, str):
                str_path += f".{item}"
            else:
                raise TypeError(
                    f"Expected path elements to be strings or integers, but got {type(item)}"
                )
    return str_path


def toml_path_from_str(path: str) -> TomlPath:
    tokens = []
    for segment in path.split("."):
        # Split each segment by bracketed chunks, e.g. "key[1]" -> ["key", "[1]"]
        parts = re.split(r"(\[\d+\])", segment)
        for p in parts:
            if not p:  # Skip empty strings
                continue
            if p.startswith("[") and p.endswith("]"):
                tokens.append(int(p[1:-1]))  # Convert "[1]" to integer 1
            else:
                tokens.append(p)
    return tuple(tokens)


def create_toml_node(
    doc: dict[str, Any],
    path: tuple[Union[str, int], ...],
    value: object,
) -> None:
    """Set a toml node at a path that consists of a sequence of keys and integer indices.
    Intermediate containers that don't yet exist will be created along the way based on the types of
    the keys. Note that this does not support TOMLDocument objects, only plain dictionaries. The
    reason is that the correct type of container to insert at intermediate nodes is ambiguous for
    TOMLDocument objects.
    """
    import tomlkit

    if isinstance(doc, tomlkit.TOMLDocument):
        raise TypeError(
            "`create_toml_node` only works on the plain dictionary representation of a TOML document."
        )
    current: Any = doc
    for i, key in enumerate(path):
        is_final_key = i == len(path) - 1
        if isinstance(key, str):
            if not isinstance(current, dict):
                raise KeyError(f"Key '{key}' not found in path: {toml_path_to_str(path)}")
            elif is_final_key:
                current[key] = value
            elif key not in current:
                current[key] = _get_new_container_node(path[i + 1])
            current = current[key]
        elif isinstance(key, int):
            if not isinstance(current, list):
                raise KeyError(f"Index '{key}' not found in path: {toml_path_to_str(path)}")
            is_key_in_range = key >= 0 and key < len(current)
            is_append_key = key == len(current)
            if is_final_key and is_key_in_range:
                current[key] = value
            elif is_final_key and is_append_key:
                current.append(value)
            elif is_key_in_range:
                current = current[key]
            elif is_append_key:
                current.append(_get_new_container_node(path[i + 1]))
                current = current[key]
            else:
                raise KeyError(f"Key '{key}' not found in path: {toml_path_to_str(path)}")
        else:
            raise TypeError(f"Expected key to be a string or integer, but got {type(key)}")


def _get_new_container_node(
    representative_key: Union[int, str],
) -> Union[dict[str, Any], list[Any]]:
    return [] if isinstance(representative_key, int) else {}


@contextlib.contextmanager
def modify_toml(path: Path) -> Iterator["tomlkit.TOMLDocument"]:
    import tomlkit

    toml = tomlkit.parse(path.read_text())
    yield toml
    path.write_text(tomlkit.dumps(toml))


@contextlib.contextmanager
def modify_toml_as_dict(path: Path) -> Iterator[dict[str, Any]]:  # unwrap gets the dict
    """Modify a TOML file as a plain python dict, destroying any comments or formatting.

    This is a destructive means of modifying TOML. We convert the parsed TOML document into a plain
    python object, modify it, and then write it back to the file. This will destroy comments and
    styling. It is useful mostly in a testing context where we want to e.g. set arbitrary invalid
    values in the file without worrying about the details of the TOML syntax (it has multiple kinds of
    dict-like objects, for instance).
    """
    import tomlkit

    toml_dict = load_toml_as_dict(path)
    yield toml_dict
    path.write_text(tomlkit.dumps(toml_dict))
