from dagster._grpc.server import _get_changed_defs_state_keys
from dagster_shared.serdes.objects.models.defs_state_info import DefsKeyStateInfo, DefsStateInfo


def _info(versions: dict[str, str | None]) -> DefsStateInfo:
    return DefsStateInfo(
        info_mapping={
            k: (DefsKeyStateInfo(version=v, create_timestamp=0) if v else None)
            for k, v in versions.items()
        }
    )


def test_no_changes() -> None:
    assert _get_changed_defs_state_keys(None, None) == set()
    info = _info({"a": "v1"})
    assert _get_changed_defs_state_keys(info, info) == set()


def test_added_removed_and_bumped() -> None:
    old = _info({"a": "v1", "b": "v1", "c": "v1"})
    new = _info({"a": "v1", "b": "v2", "d": "v1"})
    # b bumped, c removed, d added; a unchanged.
    assert _get_changed_defs_state_keys(old, new) == {"b", "c", "d"}


def test_old_none_treats_all_new_as_added() -> None:
    new = _info({"a": "v1", "b": "v1"})
    assert _get_changed_defs_state_keys(None, new) == {"a", "b"}


def test_new_none_treats_all_old_as_removed() -> None:
    old = _info({"a": "v1", "b": "v1"})
    assert _get_changed_defs_state_keys(old, None) == {"a", "b"}
