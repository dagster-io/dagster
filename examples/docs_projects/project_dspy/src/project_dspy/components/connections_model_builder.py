"""Connections model builder component for Dagster-based DSPy optimization."""

from .ds_py_model_builder import DSPyModelBuilder


class ConnectionsModelBuilder(DSPyModelBuilder):
    """Specialized component for building Connections solver models.

    This extends the base DSPyModelBuilder with Connections-specific defaults
    and configuration suitable for puzzle-solving tasks.
    """

    # start_connections_init
    def __init__(self, **kwargs):
        # Set Connections-specific defaults
        defaults = {
            "model_name": "connections",
            "connections_data_path": "data/Connections_Data.csv",
            "performance_threshold": 0.3,
            "optimization_enabled": True,
            "train_test_split": 0.25,
            "eval_subset_size": 30,
        }

        # Override with user-provided values
        for key, value in defaults.items():
            if key not in kwargs:
                kwargs[key] = value

        super().__init__(**kwargs)

    # end_connections_init
