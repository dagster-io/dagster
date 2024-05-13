from dataclasses import dataclass
from typing import Any, Optional, cast

from .source_position import KeyPath, SourcePosition, SourcePositionTreeNode


@dataclass(frozen=True)
class ObjectMappingContext:
    """Represents the context information for an object during the YAML object mapping process.

    This class contains information about the parent object, the current key path, and the source
    position of the object in the YAML document.

    Attributes:
        parent (Optional[Any]): The parent object of the current object.
        key_path (KeyPath): The path of keys that lead to the current object, where each element in
            the path is either a string (for dict keys) or an integer (for list indices).
        source_position (Optional[SourcePosition]): The source position of the object in the YAML
            document, if available.
    """

    parent: Optional[Any]
    key_path: KeyPath
    source_position: Optional[SourcePosition]


class HasObjectMappingContext:
    _object_mapping_context: Optional[ObjectMappingContext] = None


def populate_object_mapping_context(
    obj: Any,
    tree_node: Optional[SourcePositionTreeNode],
    parent: Optional[Any] = None,
    key_path: KeyPath = [],
) -> None:
    """Populate the ObjectMappingContext for the given object and its children.

    This function recursively traverses the object and its children, setting the
    ObjectMappingContext on each object that implements the HasObjectMappingContext protocol.

    The context is set based on the provided tree node, which contains the source position
    information for the object and its children.

    Args:
        obj (Any): The object to populate the context for.
        tree_node (Optional[SourcePositionTreeNode]): The tree node containing the source
            position information for the object and its children.
        parent (Optional[Any]): The parent object of the current object.
        key_path (KeyPath): The path of keys that lead to the current object.
    """
    if isinstance(obj, HasObjectMappingContext):
        source_position = None
        if tree_node is not None:
            source_position = tree_node.position
        context = ObjectMappingContext(parent, key_path, source_position)
        if obj._object_mapping_context is not None and obj._object_mapping_context != context:  # noqa: SLF001
            raise RuntimeError(
                "Cannot call populate_object_mapping_context() more than once on the same object"
            )
        obj._object_mapping_context = context  # noqa: SLF001

    if tree_node is None:
        return

    for child_key_segment, child_tree_node in tree_node.children.items():
        try:
            child_obj = cast(Any, obj)[child_key_segment]
        except TypeError:
            if not isinstance(child_key_segment, str):
                raise
            child_obj = getattr(obj, child_key_segment)

        populate_object_mapping_context(
            child_obj, child_tree_node, obj, key_path + [child_key_segment]
        )
