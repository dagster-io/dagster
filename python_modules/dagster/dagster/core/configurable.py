from dagster import check
'''
Configurable

This is a mixin-style addition to the core type this the allows
us to declare where a type is Configurability declaratively.
What mixin the user declares determines the config schema
for the type. Now *any* type that is Configurable can be
a config, and that config scheam is wholly disconnectedd
by its in-memory respresentation.
'''


class FieldDefinitionDictionary(dict):
    def __init__(self, ddict):
        check.dict_param(ddict, 'ddict', key_type=str, value_type=Field)
        super(FieldDefinitionDictionary, self).__init__(ddict)

    def __setitem__(self, _key, _value):
        check.failed('This dictionary is readonly')


class Configurable(object):
    @property
    def configurable_from_list(self):
        return isinstance(self, ConfigurableFromList)

    @property
    def configurable_selector_from_dict(self):
        return isinstance(self, ConfigurableSelectorFromDict)

    @property
    def configurable_from_nullable(self):
        return isinstance(self, ConfigurableFromNullable)

    @property
    def configurable_from_dict(self):
        return isinstance(self, ConfigurableFromDict)

    @property
    def configurable_from_scalar(self):
        return isinstance(self, ConfigurableFromScalar)

    @property
    def configurable_object_from_dict(self):
        return isinstance(self, ConfigurableObjectFromDict)

    @property
    def configurable_from_any(self):
        return isinstance(self, ConfigurableFromAny)

    @property
    def inner_types(self):
        return []


class ConfigurableFromScalar(Configurable):
    def construct_from_config_value(self, config_value):
        '''This function is called *after* the config value has been processed
        (error-checked and default values applied)'''
        return config_value


class ConfigurableFromAny(Configurable):
    def construct_from_config_value(self, config_value):
        '''This function is called *after* the config value has been processed
        (error-checked and default values applied)'''
        return config_value


class ConfigurableFromDict(Configurable):
    def __init__(self, fields, *args, **kwargs):
        super(ConfigurableFromDict, self).__init__(*args, **kwargs)
        self.field_dict = FieldDefinitionDictionary(fields)

    def construct_from_config_value(self, config_value):
        '''This function is called *after* the config value has been processed
        (error-checked and default values applied)'''
        return config_value

    # TODO Remove?
    @property
    def fields(self):
        return self.field_dict

    @property
    def inner_types(self):
        return list(self._uniqueify(self._inner_types()))

    def _uniqueify(self, types):
        seen = set()
        for type_ in types:
            if type_.name not in seen:
                yield type_
                seen.add(type_.name)

    def _inner_types(self):
        for field in self.field_dict.values():
            yield field.dagster_type
            for inner_type in field.dagster_type.inner_types:
                yield inner_type

    @property
    def all_fields_optional(self):
        for field in self.field_dict.values():
            if not field.is_optional:
                return False
        return True

    @property
    def field_name_set(self):
        return set(self.field_dict.keys())

    def field_named(self, name):
        check.str_param(name, 'name')
        return self.field_dict[name]

    def iterate_types(self):
        for field_type in self.field_dict.values():
            for inner_type in field_type.dagster_type.iterate_types():
                yield inner_type

        # FIXME: is_named needs to be moved into Configurable
        if self.is_named:  # pylint: disable=E1101
            yield self


class ConfigurableObjectFromDict(ConfigurableFromDict):
    pass


class ConfigurableSelectorFromDict(ConfigurableFromDict):
    '''This subclass "marks" a composite type as one where only
    one of its fields can be configured at a time. This was originally designed
    for context definition selection (only one context can be used for a particular
    pipeline invocation); this is generalization of that concept.
    '''
    pass


class ConfigurableFromList(Configurable):
    def __init__(self, inner_configurable, *args, **kwargs):
        super(ConfigurableFromList, self).__init__(*args, **kwargs)
        self.inner_configurable = check.inst_param(
            inner_configurable,
            'inner_configurable',
            Configurable,
        )

    @property
    def inner_types(self):
        return [self.inner_configurable] + list(self.inner_configurable.inner_types)


class ConfigurableFromNullable(Configurable):
    def __init__(self, inner_configurable, *args, **kwargs):
        super(ConfigurableFromNullable, self).__init__(*args, **kwargs)
        self.inner_configurable = check.inst_param(
            inner_configurable,
            'inner_configurable',
            Configurable,
        )

    @property
    def inner_types(self):
        return [self.inner_configurable] + list(self.inner_configurable.inner_types)


class __FieldValueSentinel:
    pass


class __InferOptionalCompositeFieldSentinel:
    pass


FIELD_NO_DEFAULT_PROVIDED = __FieldValueSentinel

INFER_OPTIONAL_COMPOSITE_FIELD = __InferOptionalCompositeFieldSentinel


def all_optional_type(configurable_type):
    check.inst_param(configurable_type, 'dagster_type', Configurable)

    if isinstance(configurable_type, ConfigurableObjectFromDict):
        return configurable_type.all_fields_optional
    return False


class Field:
    '''
    A Field in a DagsterCompositeType.

    Attributes:
        dagster_type (DagsterType): The type of the field.
        default_value (Any):
            If the Field is optional, a default value can be provided when the field value
            is not specified.
        is_optional (bool): Is the field optional.
        description (str): Description of the field.
    '''

    def __init__(
        self,
        dagster_type,
        default_value=FIELD_NO_DEFAULT_PROVIDED,
        is_optional=INFER_OPTIONAL_COMPOSITE_FIELD,
        description=None,
    ):
        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', Configurable)
        self.description = check.opt_str_param(description, 'description')
        if is_optional == INFER_OPTIONAL_COMPOSITE_FIELD:
            is_optional = all_optional_type(dagster_type)
            if is_optional is True:
                from .evaluator import hard_create_config_value
                self._default_value = lambda: hard_create_config_value(dagster_type, None)
            else:
                self._default_value = default_value
        else:
            is_optional = check.bool_param(is_optional, 'is_optional')
            self._default_value = default_value

        if is_optional is False:
            check.param_invariant(
                default_value == FIELD_NO_DEFAULT_PROVIDED,
                'default_value',
                'required arguments should not specify default values',
            )

        self.is_optional = is_optional

    @property
    def default_provided(self):
        '''Was a default value provided

        Returns:
            bool: Yes or no
        '''
        return self._default_value != FIELD_NO_DEFAULT_PROVIDED

    @property
    def default_value(self):
        check.invariant(
            self.default_provided,
            'Asking for default value when none was provided',
        )

        if callable(self._default_value):
            return self._default_value()

        return self._default_value

    @property
    def default_value_as_str(self):
        check.invariant(
            self.default_provided,
            'Asking for default value when none was provided',
        )

        if callable(self._default_value):
            return repr(self._default_value)

        return str(self._default_value)
