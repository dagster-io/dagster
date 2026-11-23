"""Mock definitions shaped like a large, check-heavy, partitioned code location.

The shape follows a large production code location (~7.9k assets, ~57k asset checks, ~1.8k
statically partitioned assets), so that the size and serialization cost of its repository snapshot
can be measured:

* assets are produced by multi-assets grouped in ~350 groups, with 4-element asset keys;
* ~24% of assets are statically partitioned, with heavy-tailed partition counts (median ~23,
  p90 ~140, max ~3.5k keys of ~16 characters);
* ~24% of assets carry ~30 asset checks each, drawn from a small vocabulary of check names and
  descriptions; checks on partitioned assets share the asset's partitions definition;
* assets carry ~7 metadata entries (code references, URIs, configuration flags, JSON blobs) and a
  ~200 character description;
* a few hundred partitioned asset jobs select whole groups.
"""

import random
import warnings
from collections.abc import Sequence

import dagster as dg

NUM_TOP_GROUPS = 20
NUM_GROUPS = 350
ASSETS_PER_GROUP = 22
CHECKED_ASSET_FRACTION = 0.24
PARTITIONED_GROUP_FRACTION = 0.24
NUM_JOBS = 260
CHECK_VOCABULARY = [f"checks__heuristic_{i:03d}" for i in range(110)] + [
    f"rubrics__judge_{i:02d}" for i in range(10)
]
CHECK_DESCRIPTIONS = [
    "Passes when no execution errors occurred.",
    "Passes when at most 5.00% of judged rows failed to evaluate.",
    "More than the configured fraction of terminal episodes must finish successfully.",
]
RESOURCE_KEYS = ["io_manager", "warehouse", "object_store", "scheduler", "llm"]
STAGES = ["instances", "generate", "checks", "judges", "lang", "quality", "export"]
CONFIG_FLAGS = [
    "flagging_mode",
    "filter_mode",
    "fixes_preset",
    "checks_preset",
    "blocking_evaluation_checks",
    "max_error_fraction",
    "short_circuit_judge",
    "partition_column",
    "num_buckets",
    "bucket_key",
    "local_media",
]


class ComponentOrigin:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return self.name


def _partition_count(rng: random.Random) -> int:
    # Heavy tail: median ~20, p90 ~140, max ~3.5k.
    roll = rng.random()
    if roll < 0.55:
        return rng.randint(1, 23)
    if roll < 0.93:
        return rng.randint(24, 150)
    if roll < 0.995:
        return rng.randint(150, 800)
    return rng.randint(800, 3500)


def _partitions_def(rng: random.Random, group: str) -> dg.PartitionsDefinition:
    roll = rng.random()
    if roll < 0.04:
        return dg.MonthlyPartitionsDefinition(start_date="2017-01-01")
    if roll < 0.07:
        return dg.MultiPartitionsDefinition(
            {
                "month": dg.MonthlyPartitionsDefinition(start_date="2017-01-01"),
                "variant": dg.StaticPartitionsDefinition(
                    [f"{group.replace('/', '_')}_variant_{i}--high" for i in range(12)]
                ),
            }
        )
    count = _partition_count(rng)
    return dg.StaticPartitionsDefinition(
        [f"shard-{group[-4:]}-{i:05d}".replace("/", "_") for i in range(count)]
    )


def _metadata(rng: random.Random, key: dg.AssetKey, group: str, checked: bool) -> dict:
    path = "/".join(key.path)
    metadata: dict = {
        "dagster/code_references": dg.CodeReferencesMetadataValue(
            code_references=[
                dg.UrlCodeReference(
                    url=f"https://github.com/example-org/monorepo/tree/687ddc3c94c79826714d0096d5691ac8fc91741a/projects/datasets/defs/{group}/defs.yaml#L{rng.randint(1, 400)}"
                )
            ]
        ),
        "dagster/uri": dg.MetadataValue.url(f"http://go/s/prod.{path.replace('/', '.')}"),
        "dagster/component_origin": dg.MetadataValue.text(
            rng.choice(["QualityCheckedDatasets", "TrainingDatasets", "JsonlDatasets"])
        ),
        "pyspark/cluster": dg.MetadataValue.text("spark-connect-datasets"),
        "example.ai/jsonl-row-model": dg.MetadataValue.text("example.schemas.ConversationRow"),
    }
    if rng.random() < 0.25:
        metadata["example/iceberg/storage_partition_contract"] = dg.MetadataValue.json(
            {
                "dimensions": [{"name": "partition", "storage_field": "partition"}],
                "physical_fields": {
                    "partition": {"source_column": "partition", "transform": "identity"}
                },
                "version": 7,
            }
        )
    if checked:
        for flag in CONFIG_FLAGS:
            metadata[f"example.ai/quality-config/{flag}"] = dg.MetadataValue.text(
                rng.choice(["default", "strict", "none", "0.05"])
            )
        metadata["example.ai/quality-config/reexport_checks"] = dg.MetadataValue.json(
            sorted(rng.sample(CHECK_VOCABULARY, 8))
        )
    return metadata


def _make_multi_asset(
    rng: random.Random,
    group: str,
    op_name: str,
    keys: Sequence[dg.AssetKey],
    upstream: Sequence[dg.AssetKey],
    partitions_def: dg.PartitionsDefinition | None,
    checked: set[dg.AssetKey],
):
    owner = rng.choice(["team:datasets", "team:evals", "team:platform"])
    specs = [
        dg.AssetSpec(
            key=key,
            deps=upstream,
            group_name=group,
            description=(
                f"Dataset {'/'.join(key.path)} produced by stage {key.path[-1]}. "
                "Rows are conversations with one problem each, with judge annotations and "
                f"quality signals stored in row metadata (variant {rng.randint(0, 10**6)})."
            ),
            metadata=_metadata(rng, key, group, key in checked),
            tags={
                "component": "QualityCheckedDatasets",
                "dagster/kind/jsonl": "",
                "dagster/kind/spark": "",
                "example.ai/managed-by": "example",
            },
            owners=[owner],
            code_version=(f"{rng.getrandbits(256):064x}" if rng.random() < 0.45 else None),
        )
        for key in keys
    ]
    check_specs = [
        dg.AssetCheckSpec(
            name=name,
            asset=key,
            description=rng.choices(CHECK_DESCRIPTIONS, weights=[95, 3, 2])[0],
            blocking=rng.random() < 0.55,
            partitions_def=partitions_def,
        )
        for key in keys
        if key in checked
        for name in rng.sample(CHECK_VOCABULARY, rng.randint(15, 49))
    ]

    @dg.multi_asset(
        name=op_name,
        specs=specs,
        check_specs=check_specs,
        partitions_def=partitions_def,
        required_resource_keys=set(rng.sample(RESOURCE_KEYS, 2)),
        pool=f"asset/{op_name}",
        can_subset=True,
    )
    def _compute(context):
        raise NotImplementedError()

    return _compute


def build_definitions(seed: int = 0, num_groups: int = NUM_GROUPS) -> dg.Definitions:
    warnings.filterwarnings("ignore", category=dg.BetaWarning)
    warnings.filterwarnings("ignore", category=dg.PreviewWarning)
    rng = random.Random(seed)
    assets = []
    jobs = []
    for group_index in range(num_groups):
        top = f"top_{group_index % NUM_TOP_GROUPS:02d}"
        group = f"{top}/{1100 + group_index}_run/variant_{group_index}"
        partitions_def = (
            _partitions_def(rng, group) if rng.random() < PARTITIONED_GROUP_FRACTION else None
        )
        prefix = ["datasets", top, f"run_{group_index:04d}"]
        keys = [
            dg.AssetKey([*prefix, f"{rng.choice(STAGES)}_{i:02d}"]) for i in range(ASSETS_PER_GROUP)
        ]
        checked = {key for key in keys if rng.random() < CHECKED_ASSET_FRACTION}
        upstream: list[dg.AssetKey] = []
        # ~1.3 assets per op on average, with a few large multi-assets.
        index = 0
        op_index = 0
        while index < len(keys):
            size = 1 if rng.random() < 0.8 else rng.randint(2, 6)
            chunk = keys[index : index + size]
            op_name = "__".join([*prefix, f"op_{op_index}"])
            assets.append(
                _make_multi_asset(
                    rng, group, op_name, chunk, upstream[-1:], partitions_def, checked
                )
            )
            upstream = list(chunk)
            index += size
            op_index += 1
        if partitions_def is not None and len(jobs) < NUM_JOBS:
            jobs.append(
                dg.define_asset_job(
                    name="__".join([*prefix, "job"]),
                    selection=dg.AssetSelection.groups(group),
                    partitions_def=partitions_def,
                )
            )
    return dg.Definitions(
        assets=assets,
        jobs=jobs,
        resources={
            **{key: dg.ResourceDefinition.none_resource() for key in RESOURCE_KEYS},
            "io_manager": dg.InMemoryIOManager(),
        },
    )


defs = build_definitions()
