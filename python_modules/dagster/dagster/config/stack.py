from collections import namedtuple

from dagster import check

from .config_type import ConfigType, ConfigTypeKind
from .field import check_field_param


class EvaluationStack(namedtuple('_EvaluationStack', 'config_type entries')):
    def __new__(cls, config_type, entries):
        return super(EvaluationStack, cls).__new__(
            cls,
            check.inst_param(config_type, 'config_type', ConfigType),
            check.list_param(entries, 'entries', of_type=EvaluationStackEntry),
        )

    @property
    def levels(self):
        return [
            entry.field_name
            for entry in self.entries
            if isinstance(entry, EvaluationStackPathEntry)
        ]

    @property
    def type_in_context(self):
        ttype = self.entries[-1].config_type if self.entries else self.config_type
        # TODO: should we be unwrapping the nullable type here?
        if ttype.kind == ConfigTypeKind.NONEABLE:
            return ttype.inner_type
        else:
            return ttype

    def for_new_type(self, config_type):
        return EvaluationStack(config_type=config_type, entries=self.entries)

    def for_field(self, field_name, field_def):
        return EvaluationStack(
            config_type=self.config_type,
            entries=self.entries + [EvaluationStackPathEntry(field_name, field_def)],
        )

    def for_array_index(self, list_index):
        list_type = self.type_in_context
        check.invariant(list_type.kind == ConfigTypeKind.ARRAY)
        return EvaluationStack(
            config_type=self.config_type,
            entries=self.entries + [EvaluationStackListItemEntry(list_type.inner_type, list_index)],
        )


class EvaluationStackEntry(object):  # marker interface
    pass


class EvaluationStackPathEntry(
    namedtuple('_EvaluationStackEntry', 'field_name field_def'), EvaluationStackEntry
):
    def __new__(cls, field_name, field_def):
        return super(EvaluationStackPathEntry, cls).__new__(
            cls,
            check.str_param(field_name, 'field_name'),
            check_field_param(field_def, 'field_def'),
        )

    @property
    def config_type(self):
        return self.field_def.config_type


class EvaluationStackListItemEntry(
    namedtuple('_EvaluationStackListItemEntry', 'config_type list_index'), EvaluationStackEntry
):
    def __new__(cls, config_type, list_index):
        check.int_param(list_index, 'list_index')
        check.param_invariant(list_index >= 0, 'list_index')
        return super(EvaluationStackListItemEntry, cls).__new__(
            cls, check.inst_param(config_type, 'config_type', ConfigType), list_index
        )


def get_friendly_path_msg(stack):
    return get_friendly_path_info(stack)[0]


def get_friendly_path_info(stack):
    if not stack.entries:
        path = ''
        path_msg = 'at document config root.'  # https://github.com/dagster-io/dagster/issues/2117
    else:
        comps = ['root']
        for entry in stack.entries:
            if isinstance(entry, EvaluationStackPathEntry):
                comp = ':' + entry.field_name
                comps.append(comp)
            elif isinstance(entry, EvaluationStackListItemEntry):
                comps.append('[{i}]'.format(i=entry.list_index))
            else:
                check.failed('unsupported')

        path = ''.join(comps)
        path_msg = 'at path ' + path
    return path_msg, path
