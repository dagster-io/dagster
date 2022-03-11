from abc import ABC, abstractmethod


class InputManager(ABC):
    """
    Base interface for classes that are responsible for loading solid inputs.
    """

    @abstractmethod
    def load_input(self, context):
        """The user-defined read method that loads an input to a solid.

        Args:
            context (InputContext): The input context.

        Returns:
            Any: The data object.
        """
