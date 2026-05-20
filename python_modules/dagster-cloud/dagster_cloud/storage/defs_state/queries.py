GET_LATEST_DEFS_STATE_INFO_QUERY = """
    query getLatestDefsStateInfo {
        latestDefsStateInfo
    }
"""

SET_LATEST_VERSION_MUTATION = """
    mutation setLatestDefsStateVersion($key: String!, $version: String!) {
        defsState {
            setLatestDefsStateVersion(key: $key, version: $version) {
                ok
            }
        }
    }
"""
