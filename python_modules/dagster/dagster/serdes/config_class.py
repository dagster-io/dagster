import importlib
from abc import ABC, abstractmethod, abstractproperty
from typing import NamedTuple

import yaml
from dagster import check

from .serdes import whitelist_for_serdes


@whitelist_for_serdes
class ConfigurableClassData(
    NamedTuple(
        "_ConfigurableClassData",
        [
            ("module_name", str),
            ("class_name", str),
            ("config_yaml", str),
        ],
    )
):
    """Serializable tuple describing where to find a class and the config fragment that should
    be used to instantiate it.

    Users should not instantiate this class directly.

    Classes intended to be serialized in this way should implement the
    :py:class:`dagster.serdes.ConfigurableClass` mixin.
    """

    def __new__(cls, module_name, class_name, config_yaml):
        return super(ConfigurableClassData, cls).__new__(
            cls,
            check.str_param(module_name, "module_name"),
            check.str_param(class_name, "class_name"),
            check.str_param(config_yaml, "config_yaml"),
        )

    def info_dict(self):
        return {
            "module": self.module_name,
            "class": self.class_name,
            "config": yaml.safe_load(self.config_yaml),
        }

    def rehydrate(self):
        from dagster.core.errors import DagsterInvalidConfigError
        from dagster.config.field import resolve_to_config_type
        from dagster.config.validate import process_config

        try:
            module = importlib.import_module(self.module_name)
        except ModuleNotFoundError:
            check.failed(
                "Couldn't import module {module_name} when attempting to load the "
                "configurable class {configurable_class}".format(
                    module_name=self.module_name,
                    configurable_class=self.module_name + "." + self.class_name,
                )
            )
        try:
            klass = getattr(module, self.class_name)
        except AttributeError:
            check.failed(
                "Couldn't find class {class_name} in module when attempting to load the "
                "configurable class {configurable_class}".format(
                    class_name=self.class_name,
                    configurable_class=self.module_name + "." + self.class_name,
                )
            )

        if not issubclass(klass, ConfigurableClass):
            raise check.CheckError(
                klass,
                "class {class_name} in module {module_name}".format(
                    class_name=self.class_name, module_name=self.module_name
                ),
                ConfigurableClass,
            )

        config_dict = yaml.safe_load(self.config_yaml)
        result = process_config(resolve_to_config_type(klass.config_type()), config_dict)
        if not result.success:
            raise DagsterInvalidConfigError(
                "Errors whilst loading configuration for {}.".format(klass.config_type()),
                result.errors,
                config_dict,
            )
        return klass.from_config_value(self, result.value)


class ConfigurableClass(ABC):
    """Abstract mixin for classes that can be loaded from config.

    This supports a powerful plugin pattern which avoids both a) a lengthy, hard-to-synchronize list
    of conditional imports / optional extras_requires in dagster core and b) a magic directory or
    file in which third parties can place plugin packages. Instead, the intention is to make, e.g.,
    run storage, pluggable with a config chunk like:

    .. code-block:: yaml

        run_storage:
            module: very_cool_package.run_storage
            class: SplendidRunStorage
            config:
                magic_word: "quux"

    This same pattern should eventually be viable for other system components, e.g. engines.

    The ``ConfigurableClass`` mixin provides the necessary hooks for classes to be instantiated from
    an instance of ``ConfigurableClassData``.

    Pieces of the Dagster system which we wish to make pluggable in this way should consume a config
    type such as:

    .. code-block:: python

        {'module': str, 'class': str, 'config': Field(Permissive())}

    """

    @abstractproperty
    def inst_data(self):
        """
        Subclass must be able to return the inst_data as a property if it has been constructed
        through the from_config_value code path.
        """

    @classmethod
    @abstractmethod
    def config_type(cls):
        """dagster.ConfigType: The config type against which to validate a config yaml fragment
        serialized in an instance of ``ConfigurableClassData``.
        """

    @staticmethod
    @abstractmethod
    def from_config_value(inst_data, config_value):
        """New up an instance of the ConfigurableClass from a validated config value.

        Called by ConfigurableClassData.rehydrate.

        Args:
            config_value (dict): The validated config value to use. Typically this should be the
                ``value`` attribute of a
                :py:class:`~dagster.core.types.evaluator.evaluation.EvaluateValueResult`.


        A common pattern is for the implementation to align the config_value with the signature
        of the ConfigurableClass's constructor:

        .. code-block:: python

            @staticmethod
            def from_config_value(inst_data, config_value):
                return MyConfigurableClass(inst_data=inst_data, **config_value)

        """


def class_from_code_pointer(module_name, class_name):
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        check.failed(
            "Couldn't import module {module_name} when attempting to load the "
            "class {klass}".format(
                module_name=module_name,
                klass=module_name + "." + class_name,
            )
        )
    try:
        return getattr(module, class_name)
    except AttributeError:
        check.failed(
            "Couldn't find class {class_name} in module when attempting to load the "
            "class {klass}".format(
                class_name=class_name,
                klass=module_name + "." + class_name,
            )
        )
