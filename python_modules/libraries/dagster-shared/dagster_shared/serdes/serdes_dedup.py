from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from dagster._utils.security import non_secure_md5_hash_str

from dagster_shared import seven
from dagster_shared.serdes.serdes import (
    _WHITELIST_MAP,
    JsonSerializableValue,
    PackableValue,
    SerializableObject,
    UnpackContext,
    UnpackedValue,
    WhitelistMap,
    _root,
    _transform_for_serialization,
    unpack_value,
)
from dagster_shared.utils.cached_method import cached_method

_UNSET_SENTINEL = "__dg_unset__"
_OBJ_ID = "__dgoi"


@dataclass
class PackedObjects:
    cname: str
    fields: list[str]
    values: list[list[JsonSerializableValue]]

    def to_json(self):
        return [self.cname, self.fields, self.values]

    @classmethod
    def from_json(cls, json: list[Any]):
        return cls(cname=json[0], fields=json[1], values=json[2])


@dataclass
class SerializationPackingContext:
    whitelist_map: WhitelistMap
    unpack_context: UnpackContext = field(default_factory=UnpackContext)

    # keeps track of where a given object id lives
    obj_locs: dict[str, tuple[str, int]] = field(default_factory=dict)
    # keeps track of the values of a given object id
    obj_vals: dict[str, PackedObjects] = field(default_factory=dict)

    def to_json(self):
        return [self.obj_locs, {k: v.to_json() for k, v in self.obj_vals.items()}]

    @classmethod
    def from_json(cls, json: list[Any], whitelist_map: WhitelistMap):
        return cls(
            obj_locs=json[0],
            obj_vals={k: PackedObjects.from_json(v) for k, v in json[1].items()},
            whitelist_map=whitelist_map,
        )

    @cached_method
    def _unpack_object_id(
        self,
        obj_id: str,
    ) -> UnpackedValue:
        obj_loc = self.obj_locs[obj_id]
        container = self.obj_vals[obj_loc[0]]

        # reconstruct the fields dictionary of this object
        fields_dict: dict[str, Any] = {"__class__": obj_loc[0]}
        for fname, value in zip(container.fields, container.values[obj_loc[1]]):
            if value == _UNSET_SENTINEL:
                continue
            fields_dict[fname] = self.unpack_value(value)

        return self.unpack_value(fields_dict)

    def _unpack_object(self, val: dict) -> UnpackedValue:
        if _OBJ_ID in val:
            # construct an unpacked dictionary of the expected shape
            obj_id = val[_OBJ_ID]
            return self._unpack_object_id(obj_id)
        else:
            return unpack_value(val, whitelist_map=self.whitelist_map, context=self.unpack_context)

    def unpack_value(self, val: JsonSerializableValue) -> UnpackedValue:
        if isinstance(val, list):
            return [self.unpack_value(item) for item in val]

        if isinstance(val, dict):
            unpacked_vals = {k: self.unpack_value(v) for k, v in val.items()}
            return self._unpack_object(unpacked_vals)

        return val

    def add_obj(
        self,
        obj: SerializableObject,
        descent_path: str,
        object_handler: Callable[[SerializableObject, WhitelistMap, str], Any],
    ) -> Iterator[tuple[str, JsonSerializableValue]]:
        klass_name = obj.__class__.__name__
        serializer = self.whitelist_map.object_serializers[klass_name]
        item_iter = serializer.pack_items(obj, self.whitelist_map, object_handler, descent_path)

        try:
            obj_id = non_secure_md5_hash_str(f"{klass_name}:{hash(obj)}".encode())[:8]
        except TypeError:
            # not a hashable type, just pack the items directly
            yield from item_iter
            return

        # need to create an entry for this object id
        if obj_id not in self.obj_locs:
            field_values = dict(item_iter)

            # create an entry for this object type if it doesn't exist
            if klass_name not in self.obj_vals:
                self.obj_vals[klass_name] = PackedObjects(
                    klass_name, list(sorted(field_values.keys())), []
                )

            packed_objs = self.obj_vals[klass_name]

            packed_objs.values.append(
                [field_values.get(fname, _UNSET_SENTINEL) for fname in packed_objs.fields]
            )

            self.obj_locs[obj_id] = (klass_name, len(packed_objs.values) - 1)

        yield (_OBJ_ID, obj_id)


def _build_object_handler(
    context: SerializationPackingContext,
) -> Callable[[SerializableObject, WhitelistMap, str], Any]:
    def fn(obj: SerializableObject, whitelist_map: WhitelistMap, descent_path: str):
        return {k: v for k, v in context.add_obj(obj, descent_path, fn)}

    return fn


def serialize_value_with_packing(
    val: PackableValue,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
    **json_kwargs: Any,
) -> str:
    packing_context = SerializationPackingContext(whitelist_map=whitelist_map)
    object_handler = _build_object_handler(packing_context)
    serializable_value = _transform_for_serialization(
        val,
        whitelist_map,
        object_handler,
        _root(val),
    )
    return f"[{seven.json.dumps(serializable_value, **json_kwargs)}, {seven.json.dumps(packing_context.to_json())}]"


def deserialize_value_with_packing(
    val: str,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
) -> Any:
    deserialized_value = seven.json.loads(val)
    root_val = deserialized_value[0]
    packing_context = SerializationPackingContext.from_json(deserialized_value[1], whitelist_map)
    # print("PACKING CONTEXT: ", packing_context)
    return packing_context.unpack_value(root_val)
