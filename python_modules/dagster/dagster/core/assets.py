from collections import namedtuple

from dagster import check
from dagster.serdes import deserialize_json_to_dagster_namedtuple, whitelist_for_serdes


@whitelist_for_serdes
class AssetDetails(namedtuple("_AssetDetails", "last_wipe_timestamp")):
    """
    Set of asset fields that do not change with every materialization.  These are generally updated
    on some non-materialization action (e.g. wipe)
    """

    def __new__(cls, last_wipe_timestamp=None):
        check.opt_float_param(last_wipe_timestamp, "last_wipe_timestamp")
        return super(AssetDetails, cls).__new__(cls, last_wipe_timestamp)

    @staticmethod
    def from_db_string(db_string):
        if not db_string:
            return None

        details = deserialize_json_to_dagster_namedtuple(db_string)
        if not isinstance(details, AssetDetails):
            return None

        return details
