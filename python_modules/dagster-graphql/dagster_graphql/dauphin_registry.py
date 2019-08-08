'''
Dauphin is wrapper module around graphene meant to provide a couple additional
features. Most importantly is a type registry. Instead of referring to
the class that corresponds to the GraphQL type everywhere, you are instead
allows to use the GraphQL string. This solves an immediate short term problem
in that it is quite irritating to manage dependencies in a graphql schema
where the types refer to each other in cyclic fashion. Breaking up a schema
into multiple files without this feature (Python has no notion of forward
declarations) is difficult.

Dauphin is meant to totally wrap graphene. That means if you are viewing a code
sample online or within the graphene docs, one should be be able use
dauphin.ChooseYourClass instead of graphene.ChooseYourClass.

We also use dauphin as disintermediation layer between our application code and
graphene in places where we want additional strictness or more convenient idioms.

e.g.

dauphin.non_null_list(dauphin.String)

as opposed to

graphene.NonNull(graphene.List(graphene.NonNull(graphene.String)))

'''
from functools import partial

import graphene
from graphene.types.definitions import GrapheneGraphQLType, GrapheneObjectType, GrapheneUnionType
from graphene.types.enum import EnumMeta
from graphene.types.generic import GenericScalar
from graphene.types.typemap import TypeMap as GrapheneTypeMap
from graphene.types.typemap import resolve_type
from graphene.utils.subclass_with_meta import SubclassWithMeta_Meta
from graphql.type.introspection import IntrospectionSchema

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

# we change map to map_ in construct_union override because of collision with built-in
# pylint: disable=W0221


def get_meta(graphene_type):
    return graphene_type._meta  # pylint: disable=W0212


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

        # Not looping over GRAPHENE_TYPES in order to not fool lint
        self.ObjectType = create_registering_class(graphene.ObjectType, registering_metaclass)
        self.InputObjectType = create_registering_class(
            graphene.InputObjectType, registering_metaclass
        )
        self.Interface = create_registering_class(graphene.Interface, registering_metaclass)
        self.Scalar = create_registering_class(graphene.Scalar, registering_metaclass)

        # Not looping over GRAPHENE_BUILTINS in order to not fool lint
        self.String = graphene.String
        self.addType(graphene.String)
        self.Int = graphene.Int
        self.addType(graphene.Int)
        self.Float = graphene.Float
        self.addType(graphene.Float)
        self.Boolean = graphene.Boolean
        self.addType(graphene.Boolean)
        self.ID = graphene.ID
        self.addType(graphene.ID)
        self.GenericScalar = GenericScalar
        self.addType(GenericScalar)

    def create_schema(self):
        return DauphinSchema(
            query=self.getType('Query'),
            mutation=self.getTypeOrNull('Mutation'),
            subscription=self.getTypeOrNull('Subscription'),
            types=self.getAllImplementationTypes(),
            registry=self,
        )

    def getTypeOrNull(self, typeName):
        return self._typeMap.get(typeName)

    def getType(self, typeName):
        graphene_type = self.getTypeOrNull(typeName)
        if not graphene_type:
            raise Exception('No such type {typeName}.'.format(typeName=typeName))
        return graphene_type

    def getAllTypes(self):
        return self._typeMap.values()

    def getAllImplementationTypes(self):
        return [t for t in self._typeMap.values() if issubclass(t, self.ObjectType)]

    def addType(self, graphene_type):
        meta = get_meta(graphene_type)
        if meta:
            if not graphene_type in self._typeMap:
                self._typeMap[meta.name] = graphene_type
            else:
                raise Exception(
                    'Type {typeName} already exists in the registry.'.format(typeName=meta.name)
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
        initial_types = [self._query, self._mutation, self._subscription, IntrospectionSchema]
        if self.types:
            initial_types += self.types
        self._type_map = DauphinTypeMap(
            initial_types,
            auto_camelcase=self.auto_camelcase,
            schema=self,
            typeRegistry=self._typeRegistry,
        )

    def type_named(self, name):
        return getattr(self, name)


class DauphinTypeMap(GrapheneTypeMap):
    def __init__(self, types, typeRegistry=None, **kwargs):
        self._typeRegistry = typeRegistry
        super(DauphinTypeMap, self).__init__(types, **kwargs)

    def construct_object_type(self, map_, graphene_type):
        type_meta = get_meta(graphene_type)
        if type_meta.name in map_:
            mapped_type = map_[get_meta(graphene_type).name]
            if isinstance(mapped_type, GrapheneGraphQLType):
                assert mapped_type.graphene_type == graphene_type, (
                    "Found different types with the same name in the schema: {}, {}."
                ).format(mapped_type.graphene_type, graphene_type)
            return mapped_type

        # TODO the codepath below appears to be untested

        def interfaces():
            interfaces = []
            for interface in type_meta.interfaces:
                if isinstance(interface, str):
                    interface = self._typeRegistry.getType(interface)
                self.graphene_reducer(map_, interface)
                internal_type = map_[get_meta(interface).name]
                assert internal_type.graphene_type == interface
                interfaces.append(internal_type)
            return interfaces

        if type_meta.possible_types:
            # FIXME: is_type_of_from_possible_types does not exist
            # is_type_of = partial(is_type_of_from_possible_types, type_meta.possible_types)
            raise Exception('Not sure what is going on here. Untested codepath')
        else:
            is_type_of = type.is_type_of

        return GrapheneObjectType(
            graphene_type=type,
            name=type_meta.name,
            description=type_meta.description,
            fields=partial(self.construct_fields_for_type, map_, type),
            is_type_of=is_type_of,
            interfaces=interfaces,
        )

    def construct_union(self, map_, graphene_type):
        union_resolve_type = None
        type_meta = get_meta(graphene_type)
        if graphene_type.resolve_type:
            union_resolve_type = partial(
                resolve_type, graphene_type.resolve_type, map_, type_meta.name
            )

        def types():
            union_types = []
            for objecttype in type_meta.types:
                if isinstance(objecttype, str):
                    objecttype = self._typeRegistry.getType(objecttype)
                self.graphene_reducer(map_, objecttype)
                internal_type = map_[get_meta(objecttype).name]
                assert internal_type.graphene_type == objecttype
                union_types.append(internal_type)
            return union_types

        return GrapheneUnionType(
            graphene_type=graphene_type,
            name=type_meta.name,
            description=type_meta.description,
            types=types,
            resolve_type=union_resolve_type,
        )


def create_registering_metaclass(registry):
    class RegisteringMetaclass(SubclassWithMeta_Meta):
        def __init__(cls, name, bases, namespaces):
            super(RegisteringMetaclass, cls).__init__(name, bases, namespaces)
            if any(base for base in bases if getattr(base, '__dauphinCoreType', False)):
                registry.addType(cls)

    return RegisteringMetaclass


def create_registering_class(cls, metaclass):
    new_cls = metaclass(cls.__name__, (cls,), {})
    setattr(new_cls, '__dauphinCoreType', True)
    return new_cls


def create_union(metaclass, _registry):
    meta_class = type('Meta', (object,), {'types': ('__', '__')})
    Union = metaclass('Union', (graphene.Union,), {'Meta': meta_class})
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
        meta_class = type("Meta", (object,), meta_dict)
        return type(meta_class.enum.__name__, (cls,), {"Meta": meta_class})

    Enum = EnumRegisteringMetaclass('Enum', (graphene.Enum,), {'from_enum': classmethod(from_enum)})
    setattr(Enum, '__dauphinCoreType', True)
    return Enum


def get_type_fn(registry, dauphin_type):
    if isinstance(dauphin_type, str):
        return lambda: registry.getType(dauphin_type)
    else:
        return dauphin_type


def create_registry_field(registry):
    class Field(graphene.Field):
        def __init__(self, dauphin_type, *args, **kwargs):
            super(Field, self).__init__(get_type_fn(registry, dauphin_type), *args, **kwargs)

    return Field


def create_registry_argument(registry):
    class Argument(graphene.Argument):
        def __init__(self, dauphin_type, *args, **kwargs):
            super(Argument, self).__init__(get_type_fn(registry, dauphin_type), *args, **kwargs)

    return Argument


def create_registry_list(registry):
    class List(graphene.List):
        def __init__(self, of_type, *args, **kwargs):
            super(List, self).__init__(get_type_fn(registry, of_type), *args, **kwargs)

    return List


def create_registry_nonnull(registry):
    class NonNull(graphene.NonNull):
        def __init__(self, of_type, *args, **kwargs):
            super(NonNull, self).__init__(get_type_fn(registry, of_type), *args, **kwargs)

    return NonNull
