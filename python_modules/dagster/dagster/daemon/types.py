from collections import namedtuple


class DaemonHeartbeat(namedtuple("_DaemonHeartbeat", "timestamp daemon_type daemon_id info")):
    def __new__(cls, timestamp, daemon_type, daemon_id, info):
        return super(DaemonHeartbeat, cls).__new__(cls, timestamp, daemon_type, daemon_id, info)
