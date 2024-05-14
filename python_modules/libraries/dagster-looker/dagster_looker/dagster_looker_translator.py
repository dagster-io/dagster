from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Tuple

from dagster import AssetKey
from dagster._annotations import experimental, public


@experimental
class DagsterLookerTranslator:
    """Holds a set of methods that derive Dagster asset definition metadata given a representation
    of a LookML element (dashboards, explores, views).

    This class is exposed so that methods can be overriden to customize how Dagster asset metadata
    is derived.
    """

    @public
    def get_asset_key(self, lookml_element: Tuple[Path, Mapping[str, Any]]) -> AssetKey:
        """A method that takes in a dictionary representing a LookML element
        (dashboards, explores, views) and returns the Dagster asset key that represents the element.

        The LookML element is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overriden to provide a custom asset key for a LookML element.

        Args:
            lookml_element (Tuple[Path, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML element, and a dictionary representing a LookML element.

        Returns:
            AssetKey: The Dagster asset key that represents the LookML element.
        """
        lookml_element_path, lookml_element_props = lookml_element

        if lookml_element_path.suffixes == [".dashboard", ".lookml"]:
            return AssetKey(["dashboard", lookml_element_props["dashboard"]])

        if lookml_element_path.suffixes == [".view", ".lkml"]:
            return AssetKey(["view", lookml_element_props["name"]])

        if lookml_element_path.suffixes == [".model", ".lkml"]:
            return AssetKey(["explore", lookml_element_props["name"]])

        raise ValueError(f"Unsupported LookML element: {lookml_element_path}")

    @public
    def get_description(self, lookml_element: Tuple[Path, Mapping[str, Any]]) -> Optional[str]:
        """A method that takes in a dictionary representing a LookML element
        (dashboards, explores, views) and returns the Dagster asset key that represents the element.

        The LookML element is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overriden to provide a custom description for a LookML element.

        Args:
            lookml_element (Tuple[Path, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML element, and a dictionary representing a LookML element.

        Returns:
            Optional[str]: The Dagster description for the LookML element.
        """
        _, lookml_element_props = lookml_element

        return lookml_element_props.get("description")

    @public
    def get_metadata(
        self, lookml_element: Tuple[Path, Mapping[str, Any]]
    ) -> Optional[Mapping[str, Any]]:
        """A method that takes in a dictionary representing a LookML element
        (dashboards, explores, views) and returns the Dagster asset key that represents the element.

        The LookML element is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overriden to provide custom metadata for a LookML element.

        Args:
            lookml_element (Tuple[Path, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML element, and a dictionary representing a LookML element.

        Returns:
            Optional[Mapping[str, Any]]: A dictionary representing the Dagster metadata for the
                LookML element.
        """
        return None

    @public
    def get_group_name(self, lookml_element: Tuple[Path, Mapping[str, Any]]) -> Optional[str]:
        """A method that takes in a dictionary representing a LookML element
        (dashboards, explores, views) and returns the Dagster asset key that represents the element.

        The LookML element is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overriden to provide a custom group name for a LookML element.

        Args:
            lookml_element (Tuple[Path, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML element, and a dictionary representing a LookML element.

        Returns:
            Optional[str]: A Dagster group name for the LookML element.
        """
        return None

    @public
    def get_owners(self, lookml_element: Tuple[Path, Mapping[str, Any]]) -> Optional[Sequence[str]]:
        """A method that takes in a dictionary representing a LookML element
        (dashboards, explores, views) and returns the Dagster asset key that represents the element.

        The LookML element is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overriden to provide custom owners for a LookML element.

        Args:
            lookml_element (Tuple[Path, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML element, and a dictionary representing a LookML element.

        Returns:
            Optional[Sequence[str]]: A sequence of Dagster owners for the LookML element.
        """
        return None

    @public
    def get_tags(
        self, lookml_element: Tuple[Path, Mapping[str, Any]]
    ) -> Optional[Mapping[str, str]]:
        """A method that takes in a dictionary representing a LookML element
        (dashboards, explores, views) and returns the Dagster asset key that represents the element.

        The LookML element is parsed using ``lkml``. You can learn more about this here:
        https://lkml.readthedocs.io/en/latest/simple.html.

        You can learn more about LookML dashboards and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/param-lookml-dashboard.

        You can learn more about LookML explores and views and the properties available in this
        dictionary here: https://cloud.google.com/looker/docs/reference/lookml-quick-reference.

        This method can be overriden to provide custom tags for a LookML element.

        Args:
            lookml_element (Tuple[Path, Mapping[str, Any]]): A tuple with the path to file
                defining a LookML element, and a dictionary representing a LookML element.

        Returns:
            Optional[Mapping[str, str]]: A dictionary representing the Dagster tags for the
                LookML element.
        """
        return None
