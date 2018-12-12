import sys
from functools import partial
from six import with_metaclass
import graphene
from graphql.type.introspection import IntrospectionSchema
from graphene.types.generic import GenericScalar
from graphene.types.typemap import TypeMap as GrapheneTypeMap, resolve_type
from graphene.types.enum import EnumMeta
from graphene.utils.subclass_with_meta import SubclassWithMeta_Meta
from graphene.types.definitions import (
    GrapheneScalarType,
    GrapheneObjectType,
    GrapheneUnionType,
)

GRAPHENE_TYPES = [
    graphene.ObjectType,
    graphene.InputObjectType,
    graphene.Interface,
    graphene.Scalar,
]

GRAPHENE_BUILT_IN = [
    graphene.String,
    graphene.Int,
    graphene.Float,
    graphene.Boolean,
    graphene.ID,
    GenericScalar,
]


class DauphinRegistry(object):
    def __init__(self):
        self._typeMap = {}
        self.Field = create_registry_field(self)
        self.Argument = create_registry_argument(self)
        self.List = create_registry_list(self)
        self.NonNull = create_registry_nonnull(self)
        registering_metaclass = create_registering_metaclass(self)
        self.Union = create_union(registering_metaclass, self)
        self.Enum = create_enum(registering_metaclass)
        self.Mutation = graphene.Mutation
        for type in GRAPHENE_TYPES:
            setattr(self, type.__name__, create_registering_class(type, registering_metaclass))
        for type in GRAPHENE_BUILT_IN:
            setattr(self, type.__name__, type)
            self.addType(type)

    def create_schema(self):
        return DauphinSchema(
            query=self.getType('Query'),
            mutation=self.getTypeOrNull('Mutation'),
            subscription=self.getTypeOrNull('Subscription'),
            types=self.getAllImplementationTypes(),
            registry=self
        )

    def getTypeOrNull(self, typeName):
        return self._typeMap.get(typeName)

    def getType(self, typeName):
        type = self.getTypeOrNull(typeName)
        if not type:
            raise Exception('No such type {typeName}.'.format(typeName=typeName))
        else:
            return type

    def getAllTypes(self):
        return self._typeMap.values()

    def getAllImplementationTypes(self):
        return [t for t in self._typeMap.values() if issubclass(t, self.ObjectType)]

    def addType(self, type):
        if type._meta:
            if not type in self._typeMap:
                self._typeMap[type._meta.name] = type
            else:
                raise Exception(
                    'Type {typeName} already exists in the registry.'.format(
                        typeName=type._meta.name
                    )
                )
        else:
            raise Exception('Cannot add unnamed type or a non-type to registry.')

    def non_null_list(self, of_type):
        return self.NonNull(self.List(self.NonNull(of_type)))


class DauphinSchema(graphene.Schema):
    def __init__(self, registry, **kwargs):
        self._typeRegistry = registry
        super(DauphinSchema, self).__init__(**kwargs)

    def build_typemap(self):
        initial_types = [
            self._query,
            self._mutation,
            self._subscription,
            IntrospectionSchema,
        ]
        if self.types:
            initial_types += self.types
        self._type_map = DauphinTypeMap(
            initial_types,
            auto_camelcase=self.auto_camelcase,
            schema=self,
            typeRegistry=self._typeRegistry
        )


class DauphinTypeMap(GrapheneTypeMap):
    def __init__(self, types, typeRegistry=None, **kwargs):
        self._typeRegistry = typeRegistry
        super(DauphinTypeMap, self).__init__(types, **kwargs)

    def construct_object_type(self, map, type):
        if type._meta.name in map:
            _type = map[type._meta.name]
            if isinstance(_type, GrapheneGraphQLType):
                assert _type.graphene_type == type, (
                    "Found different types with the same name in the schema: {}, {}."
                ).format(_type.graphene_type, type)
            return _type

        def interfaces():
            interfaces = []
            for interface in type._meta.interfaces:
                if isinstance(interface, str):
                    interface = self._typeRegistry.getType(interface)
                self.graphene_reducer(map, interface)
                internal_type = map[interface._meta.name]
                assert internal_type.graphene_type == interface
                interfaces.append(internal_type)
            return interfaces

        if type._meta.possible_types:
            is_type_of = partial(is_type_of_from_possible_types, type._meta.possible_types)
        else:
            is_type_of = type.is_type_of

        return GrapheneObjectType(
            graphene_type=type,
            name=type._meta.name,
            description=type._meta.description,
            fields=partial(self.construct_fields_for_type, map, type),
            is_type_of=is_type_of,
            interfaces=interfaces,
        )

    def construct_union(self, map, type):
        _resolve_type = None
        if type.resolve_type:
            _resolve_type = partial(resolve_type, type.resolve_type, map, type._meta.name)

        def types():
            union_types = []
            for objecttype in type._meta.types:
                if isinstance(objecttype, str):
                    objecttype = self._typeRegistry.getType(objecttype)
                self.graphene_reducer(map, objecttype)
                internal_type = map[objecttype._meta.name]
                assert internal_type.graphene_type == objecttype
                union_types.append(internal_type)
            return union_types

        return GrapheneUnionType(
            graphene_type=type,
            name=type._meta.name,
            description=type._meta.description,
            types=types,
            resolve_type=_resolve_type,
        )


def create_registering_metaclass(registry):
    class RegisteringMetaclass(SubclassWithMeta_Meta):
        def __init__(cls, name, bases, namespaces):
            super(RegisteringMetaclass, cls).__init__(name, bases, namespaces)
            if any(base for base in bases if getattr(base, '__dauphinCoreType', False)):
                registry.addType(cls)

    return RegisteringMetaclass


def create_registering_class(cls, metaclass):
    new_cls = metaclass(cls.__name__, (cls, ), {})
    setattr(new_cls, '__dauphinCoreType', True)
    return new_cls


def create_union(metaclass, registry):
    meta_class = type('Meta', (object, ), {'types': ('__', '__')})
    Union = metaclass('Union', (graphene.Union, ), {'Meta': meta_class})
    setattr(Union, '__dauphinCoreType', True)
    return Union


def create_enum(metaclass):
    class EnumRegisteringMetaclass(metaclass, EnumMeta):
        pass

    def from_enum(cls, enum, description=None, deprecation_reason=None):
        description = description or enum.__doc__
        meta_dict = {
            "enum": enum,
            "description": description,
            "deprecation_reason": deprecation_reason,
        }
        meta_class = type("Meta", (object, ), meta_dict)
        return type(meta_class.enum.__name__, (cls, ), {"Meta": meta_class})

    Enum = EnumRegisteringMetaclass(
        'Enum', (graphene.Enum, ), {'from_enum': classmethod(from_enum)}
    )
    setattr(Enum, '__dauphinCoreType', True)
    return Enum


def create_registry_field(registry):
    class Field(graphene.Field):
        def __init__(self, type, *args, **kwargs):
            if isinstance(type, str):
                typeFn = lambda: registry.getType(type)
            else:
                typeFn = type
            super(Field, self).__init__(typeFn, *args, **kwargs)

    return Field


def create_registry_argument(registry):
    class Argument(graphene.Argument):
        def __init__(self, type, *args, **kwargs):
            if isinstance(type, str):
                typeFn = lambda: registry.getType(type)
            else:
                typeFn = type
            super(Argument, self).__init__(typeFn, *args, **kwargs)

    return Argument


def create_registry_list(registry):
    class List(graphene.List):
        def __init__(self, of_type, *args, **kwargs):
            if isinstance(of_type, str):
                typeFn = lambda: registry.getType(of_type)
            else:
                typeFn = of_type
            super(List, self).__init__(typeFn, *args, **kwargs)

    return List


def create_registry_nonnull(registry):
    class NonNull(graphene.NonNull):
        def __init__(self, of_type, *args, **kwargs):
            if isinstance(of_type, str):
                typeFn = lambda: registry.getType(of_type)
            else:
                typeFn = of_type
            super(NonNull, self).__init__(typeFn, *args, **kwargs)

    return NonNull
