from unittest.mock import MagicMock, patch

import dagster as dg
from project_atproto_dashboard.defs.ingestion import actor_feed_snapshot, starter_pack_snapshot


def _make_mock_s3():
    mock_s3_client = MagicMock()
    mock_s3 = MagicMock()
    mock_s3.get_client.return_value = mock_s3_client
    return mock_s3, mock_s3_client


def _meta_val(result: dg.MaterializeResult, key: str):
    """Extract metadata value regardless of whether it's wrapped or raw."""
    val = result.metadata[key]
    return val.value if hasattr(val, "value") else val


def test_actor_feed_snapshot_uploads_to_s3():
    mock_items = [MagicMock() for _ in range(5)]
    for i, item in enumerate(mock_items):
        item.model_dump_json.return_value = f'{{"post": "item_{i}"}}'

    mock_atproto = MagicMock()
    mock_s3, mock_s3_client = _make_mock_s3()

    with patch(
        "project_atproto_dashboard.defs.ingestion.get_all_feed_items",
        return_value=mock_items,
    ):
        context = dg.build_asset_context(partition_key="did:plc:testactor123")
        result = actor_feed_snapshot(context, mock_atproto, mock_s3)

    mock_s3_client.put_object.assert_called_once()
    assert _meta_val(result, "len_feed_items") == 5


def test_actor_feed_snapshot_uses_partition_key_as_actor():
    mock_atproto = MagicMock()
    mock_s3, _ = _make_mock_s3()

    captured_actor = {}

    def capture_feed_items(client, actor):
        captured_actor["value"] = actor
        return []

    with patch(
        "project_atproto_dashboard.defs.ingestion.get_all_feed_items",
        side_effect=capture_feed_items,
    ):
        context = dg.build_asset_context(partition_key="did:plc:specificactor")
        actor_feed_snapshot(context, mock_atproto, mock_s3)

    assert captured_actor["value"] == "did:plc:specificactor"


def test_starter_pack_snapshot_uploads_to_s3_and_returns_member_count():
    mock_members = [MagicMock() for _ in range(3)]
    for i, member in enumerate(mock_members):
        member.model_dump_json.return_value = f'{{"did": "did:plc:member_{i}"}}'
        member.subject.did = f"did:plc:member_{i}"

    mock_atproto = MagicMock()
    mock_s3, mock_s3_client = _make_mock_s3()

    starter_pack_uri = "at://did:plc:test/app.bsky.graph.starterpack/abc123"

    with patch(
        "project_atproto_dashboard.defs.ingestion.get_all_starter_pack_members",
        return_value=mock_members,
    ):
        context = dg.build_asset_context(partition_key=starter_pack_uri)
        result = starter_pack_snapshot(context, mock_atproto, mock_s3)

    mock_s3_client.put_object.assert_called_once()
    assert _meta_val(result, "len_members") == 3


def test_starter_pack_snapshot_partition_key_in_object_key():
    """Verify the starter pack URI appears in the S3 object key."""
    mock_members = [MagicMock() for _ in range(2)]
    for i, member in enumerate(mock_members):
        member.model_dump_json.return_value = f'{{"did": "did:plc:u{i}"}}'
        member.subject.did = f"did:plc:u{i}"

    mock_atproto = MagicMock()
    mock_s3, mock_s3_client = _make_mock_s3()

    starter_pack_uri = "at://did:plc:test/app.bsky.graph.starterpack/xyz"

    with patch(
        "project_atproto_dashboard.defs.ingestion.get_all_starter_pack_members",
        return_value=mock_members,
    ):
        context = dg.build_asset_context(partition_key=starter_pack_uri)
        result = starter_pack_snapshot(context, mock_atproto, mock_s3)

    call_kwargs = mock_s3_client.put_object.call_args.kwargs
    assert starter_pack_uri in call_kwargs["Key"]
    assert _meta_val(result, "len_members") == 2
