from typing import Any, Dict, NamedTuple


class CensusOutput(
    NamedTuple(
        "_CensusOutput",
        [
            ("sync_run", Dict[str, Any]),
            ("source", Dict[str, Any]),
            ("destination", Dict[str, Any]),
        ],
    )
):
    """
    Contains recorded information about the state of a Census sync after a sync completes.

    Attributes:
        sync_run (Dict[str, Any]):
            The details of the specific sync run
        source (Dict[str, Any]):
            Information about the source for the Census sync
        destination (Dict[str, Any]):
            Information about the destination for the Census sync
    """
