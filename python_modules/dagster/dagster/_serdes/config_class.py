import importlib
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Mapping,
    NamedTuple,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import Self

import dagster._check as check
from dagster._utils import convert_dagster_submodule_name
from dagster._utils.yaml_utils import load_run_config_yaml

from .serdes import (
    NamedTupleSerializer,
    whitelist_for_serdes,
)

if TYPE_CHECKING:
    from dagster._config.config_schema import UserConfigSchema

T_ConfigurableClass = TypeVar("T_ConfigurableClass")


class ConfigurableClassDataSerializer(NamedTupleSerializer["ConfigurableClassData"]):
    def after_pack(self, **packed: Any) -> Dict[str, Any]:
        packed["module_name"] = convert_dagster_submodule_name(packed["module_name"], "public")
        return packed


@whitelist_for_serdes(serializer=ConfigurableClassDataSerializer)
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

    def __new__(cls, module_name: str, class_name: str, config_yaml: str):
        return super(ConfigurableClassData, cls).__new__(
            cls,
            convert_dagster_submodule_name(check.str_param(module_name, "module_name"), "private"),
            check.str_param(class_name, "class_name"),
            check.str_param(config_yaml, "config_yaml"),
        )

    @property
    def config_dict(self) -> Mapping[str, Any]:
        return check.is_dict(load_run_config_yaml(self.config_yaml), key_type=str)

    def info_dict(self) -> Mapping[str, Any]:
        return {
            "module": self.module_name,
            "class": self.class_name,
            "config": self.config_dict,
        }

    @overload
    def rehydrate(self, as_type: Type[T_ConfigurableClass]) -> T_ConfigurableClass:
        ...

    @overload
    def rehydrate(self, as_type: None = ...) -> "ConfigurableClass":
        ...

    def rehydrate(
        self, as_type: Optional[Type[T_ConfigurableClass]] = None
    ) -> Union["ConfigurableClass", T_ConfigurableClass]:
        from dagster._config import process_config, resolve_to_config_type
        from dagster._core.errors import DagsterInvalidConfigError

        try:
            module = importlib.import_module(self.module_name)
        except ModuleNotFoundError:
            check.failed(
                f"Couldn't import module {self.module_name} when attempting to load the "
                f"configurable class {self.module_name}.{self.class_name}"
            )
        try:
            klass = getattr(module, self.class_name)
        except AttributeError:
            check.failed(
                f"Couldn't find class {self.class_name} in module when attempting to load the "
                f"configurable class {self.module_name}.{self.class_name}"
            )

        if not issubclass(klass, as_type or ConfigurableClass):
            raise check.CheckError(
                klass,
                f"class {self.class_name} in module {self.module_name}",
                ConfigurableClass,
            )

        config_dict = self.config_dict
        result = process_config(resolve_to_config_type(klass.config_type()), config_dict)
        if not result.success:
            raise DagsterInvalidConfigError(
                f"Errors whilst loading configuration for {klass.config_type()}.",
                result.errors,
                config_dict,
            )
        return klass.from_config_value(self, check.not_none(result.value))


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

    @property
    @abstractmethod
    def inst_data(self) -> Optional[ConfigurableClassData]:
        """Subclass must be able to return the inst_data as a property if it has been constructed
        through the from_config_value code path.
        """

    @classmethod
    @abstractmethod
    def config_type(cls) -> "UserConfigSchema":
        """Get the config type against which to validate a config yaml fragment.

        The only place config values matching this type are used is inside `from_config_value`. This
        is an alternative constructor for a class. It is a common pattern for the config type to
        match constructor arguments, so `from_config_value`

        The config type against which to validate a config yaml fragment
        serialized in an instance of ``ConfigurableClassData``.
        """
        ...
        # We need to raise `NotImplementedError` here because nothing prevents abstract class
        # methods from being called.
        raise NotImplementedError(f"{cls.__name__} must implement the config_type classmethod")

    @classmethod
    @abstractmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        """Create an instance of the ConfigurableClass from a validated config value.

        The config value used here should be derived from the accompanying `inst_data` argument.
        `inst_data` contains the yaml-serialized config-- this must be parsed and
        validated/normalized, then passed to this method for object instantiation. This is done in
        ConfigurableClassData.rehydrate.

        Args:
            config_value (dict): The validated config value to use. Typically this should be the
                ``value`` attribute of a
                :py:class:`~dagster._core.types.evaluator.evaluation.EvaluateValueResult`.


        A common pattern is for the implementation to align the config_value with the signature
        of the ConfigurableClass's constructor:

        .. code-block:: python

            @classmethod
            def from_config_value(cls, inst_data, config_value):
                return MyConfigurableClass(inst_data=inst_data, **config_value)

        """


def class_from_code_pointer(module_name: str, class_name: str) -> Type[object]:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        check.failed(
            "Couldn't import module {module_name} when attempting to load the class {klass}".format(
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
