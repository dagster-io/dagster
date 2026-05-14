import itertools

import pytest
from dagster import Field, In, Map, Nothing, Out, Permissive, Selector, Shape, job, op
from dagster._config import Array, Bool, Enum, EnumValue, Float, Int, Noneable, String
from dagster._core.snap import (
    DependencyStructureIndex,
    JobSnap,
    NodeInvocationSnap,
    snap_from_config_type,
)
from dagster._core.snap.dep_snapshot import (
    DependencyStructureSnapshot,
    InputHandle,
    OutputHandleSnap,
    build_dep_structure_snapshot_from_graph_def,
)
from dagster._record import replace
from dagster._serdes import serialize_pp, serialize_value
from dagster_shared.serdes import deserialize_value


def serialize_rt(value: JobSnap) -> JobSnap:
    return deserialize_value(serialize_value(value), JobSnap)


def get_noop_pipeline():
    @op
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    return noop_job


def test_empty_job_snap_snapshot(snapshot):
    snapshot.assert_match(serialize_pp(JobSnap.from_job_def(get_noop_pipeline())))


def test_empty_job_snap_props(snapshot):
    job_snapshot = JobSnap.from_job_def(get_noop_pipeline())

    assert job_snapshot.name == "noop_job"
    assert job_snapshot.description is None
    assert job_snapshot.tags == {}
    assert job_snapshot.run_tags is None

    assert job_snapshot == serialize_rt(job_snapshot)

    snapshot.assert_match(serialize_pp(job_snapshot))
    snapshot.assert_match(job_snapshot.snapshot_id)


def test_job_snap_all_props(snapshot):
    @op
    def noop_op(_):
        pass

    @job(description="desc", tags={"key": "value"})
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)

    assert job_snapshot.name == "noop_job"
    assert job_snapshot.description == "desc"
    assert job_snapshot.tags == {"key": "value"}

    assert job_snapshot == serialize_rt(job_snapshot)

    snapshot.assert_match(serialize_pp(job_snapshot))
    snapshot.assert_match(job_snapshot.snapshot_id)


def test_noop_deps_snap():
    @op
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    invocations = build_dep_structure_snapshot_from_graph_def(noop_job.graph).node_invocation_snaps
    assert len(invocations) == 1
    assert isinstance(invocations[0], NodeInvocationSnap)


def test_node_invocation_snap_tags_field_backcompat():
    # Producers commit to a JobSnap's identity by stamping `sha1(serialize(job_snap))`
    # onto the ExecutionPlanSnapshot they emit. Consumers (e.g. dagster-cloud host)
    # then deserialize the JobSnap and recompute that hash in-process — see
    # `ensure_persisted_execution_plan_snapshot`. The recomputed hash matches iff
    # `serialize(deserialize(payload)) == payload` byte-for-byte. NodeInvocationSnap.tags
    # must round-trip with whatever value the producer wrote, since older Dagster versions
    # populated it from node.tags.
    legacy_payload = (
        '{"__class__": "SolidInvocationSnap", "input_dep_snaps": [], '
        '"is_dynamic_mapped": false, "solid_def_name": "noop_op", '
        '"solid_name": "noop_op", "tags": {"dagster/compute_kind": "python"}}'
    )
    invocation = deserialize_value(legacy_payload, NodeInvocationSnap)
    assert serialize_value(invocation) == legacy_payload


def test_job_snap_legacy_payload_roundtrip_and_id_stability():
    # The JobSnap-level analog of test_node_invocation_snap_tags_field_backcompat. Pins
    # the snapshot_id of a JobSnap that mimics what an older Dagster's producer would
    # emit (NodeInvocationSnap.tags populated from node.tags), and asserts the wire
    # form round-trips byte-identically.
    #
    # Update the pinned snapshot_id only when JobSnap's wire format is intentionally
    # changed — and recognize that doing so will invalidate the snapshot_id of any
    # already-persisted JobSnaps, which can break runs launched by older code servers
    # (cf. ensure_persisted_execution_plan_snapshot).
    fresh = JobSnap.from_job_def(get_noop_pipeline())
    legacy = replace(
        fresh,
        dep_structure_snapshot=DependencyStructureSnapshot(
            node_invocation_snaps=[
                inv._replace(tags={"dagster/compute_kind": "python"})
                for inv in fresh.dep_structure_snapshot.node_invocation_snaps
            ],
        ),
    )
    legacy_payload = serialize_value(legacy)

    deserialized = deserialize_value(legacy_payload, JobSnap)
    assert serialize_value(deserialized) == legacy_payload
    assert deserialized.snapshot_id == "9c4a518cd96ce6f7230751ed3f47269e1d52b2bd"


def test_two_invocations_deps_snap(snapshot):
    @op
    def noop_op(_):
        pass

    @job
    def two_op_job():
        noop_op.alias("one")()
        noop_op.alias("two")()

    index = DependencyStructureIndex(build_dep_structure_snapshot_from_graph_def(two_op_job.graph))
    assert index.get_invocation("one")
    assert index.get_invocation("two")

    job_snapshot = JobSnap.from_job_def(two_op_job)
    assert job_snapshot == serialize_rt(job_snapshot)

    snapshot.assert_match(serialize_pp(job_snapshot))
    snapshot.assert_match(job_snapshot.snapshot_id)


def test_basic_dep():
    @op
    def return_one(_):
        return 1

    @op(ins={"value": In(int)})
    def passthrough(_, value):
        return value

    @job
    def single_dep_job():
        passthrough(return_one())

    index = DependencyStructureIndex(
        build_dep_structure_snapshot_from_graph_def(single_dep_job.graph)
    )

    assert index.get_invocation("return_one")
    assert index.get_invocation("passthrough")

    outputs = index.get_upstream_outputs("passthrough", "value")
    assert len(outputs) == 1
    assert outputs[0].node_name == "return_one"
    assert outputs[0].output_name == "result"


def test_basic_dep_fan_out(snapshot):
    @op
    def return_one(_):
        return 1

    @op(ins={"value": In(int)})
    def passthrough(_, value):
        return value

    @job
    def single_dep_job():
        return_one_result = return_one()
        passthrough.alias("passone")(return_one_result)
        passthrough.alias("passtwo")(return_one_result)

    dep_structure_snapshot = build_dep_structure_snapshot_from_graph_def(single_dep_job.graph)
    index = DependencyStructureIndex(dep_structure_snapshot)

    assert index.get_invocation("return_one")
    assert index.get_invocation("passone")
    assert index.get_invocation("passtwo")

    assert index.get_upstream_output("passone", "value") == OutputHandleSnap("return_one", "result")
    assert index.get_upstream_output("passtwo", "value") == OutputHandleSnap("return_one", "result")

    assert set(index.get_downstream_inputs("return_one", "result")) == set(
        [
            InputHandle("passthrough", "passone", "value"),
            InputHandle("passthrough", "passtwo", "value"),
        ]
    )

    assert (
        deserialize_value(serialize_value(dep_structure_snapshot), DependencyStructureSnapshot)
        == dep_structure_snapshot
    )

    job_snapshot = JobSnap.from_job_def(single_dep_job)
    assert job_snapshot == serialize_rt(job_snapshot)

    snapshot.assert_match(serialize_pp(job_snapshot))
    snapshot.assert_match(job_snapshot.snapshot_id)


def test_basic_fan_in(snapshot):
    @op(out=Out(Nothing))
    def return_nothing(_):
        return None

    @op(ins={"nothing": In(Nothing)})
    def take_nothings(_):
        return None

    @job
    def fan_in_test():
        take_nothings(
            [
                return_nothing.alias("nothing_one")(),
                return_nothing.alias("nothing_two")(),
            ]
        )

    dep_structure_snapshot = build_dep_structure_snapshot_from_graph_def(fan_in_test.graph)
    index = DependencyStructureIndex(dep_structure_snapshot)

    assert index.get_invocation("nothing_one")
    assert index.get_invocation("take_nothings")

    assert index.get_upstream_outputs("take_nothings", "nothing") == [
        OutputHandleSnap("nothing_one", "result"),
        OutputHandleSnap("nothing_two", "result"),
    ]

    assert (
        deserialize_value(serialize_value(dep_structure_snapshot), DependencyStructureSnapshot)
        == dep_structure_snapshot
    )

    job_snapshot = JobSnap.from_job_def(fan_in_test)
    assert job_snapshot == serialize_rt(job_snapshot)

    snapshot.assert_match(serialize_pp(job_snapshot))
    snapshot.assert_match(job_snapshot.snapshot_id)


def _dict_has_stable_hashes(hydrated_map, snapshot_config_snap_map):
    assert isinstance(hydrated_map, (Shape, Permissive, Selector))
    assert hydrated_map.key in snapshot_config_snap_map
    for field in hydrated_map.fields.values():
        assert field.config_type.key in snapshot_config_snap_map


def _array_has_stable_hashes(hydrated_array, snapshot_config_snap_map):
    assert isinstance(hydrated_array, Array)
    assert hydrated_array.key in snapshot_config_snap_map
    assert hydrated_array.inner_type.key in snapshot_config_snap_map


def _map_has_stable_hashes(hydrated_map, snapshot_config_snap_map):
    assert isinstance(hydrated_map, Map)
    assert hydrated_map.key in snapshot_config_snap_map
    assert hydrated_map.inner_type.key in snapshot_config_snap_map
    assert hydrated_map.key_type.key in snapshot_config_snap_map


def test_deserialize_op_def_snaps_default_field():
    @op(
        config_schema={
            "foo": Field(str, is_required=False, default_value="hello"),
            "bar": Field(str),
        }
    )
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, Shape)
    assert isinstance(recevied_config_type.fields["foo"].config_type, String)
    assert isinstance(recevied_config_type.fields["bar"].config_type, String)
    assert not recevied_config_type.fields["foo"].is_required
    assert recevied_config_type.fields["foo"].default_value == "hello"
    _dict_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_node_def_snaps_enum():
    @op(
        config_schema=Field(
            Enum("CowboyType", [EnumValue("good"), EnumValue("bad"), EnumValue("ugly")])
        )
    )
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, Enum)
    assert recevied_config_type.given_name == "CowboyType"
    assert all(
        enum_value.config_value in ("good", "bad", "ugly")
        for enum_value in recevied_config_type.enum_values
    )


def test_deserialize_node_def_snaps_strict_shape():
    @op(config_schema={"foo": Field(str, is_required=False), "bar": Field(str)})
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, Shape)
    assert isinstance(recevied_config_type.fields["foo"].config_type, String)
    assert isinstance(recevied_config_type.fields["bar"].config_type, String)
    assert not recevied_config_type.fields["foo"].is_required
    _dict_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_node_def_snaps_selector():
    @op(config_schema=Selector({"foo": Field(str), "bar": Field(int)}))
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, Selector)
    assert isinstance(recevied_config_type.fields["foo"].config_type, String)
    assert isinstance(recevied_config_type.fields["bar"].config_type, Int)
    _dict_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_op_def_snaps_permissive():
    @op(config_schema=Field(Permissive({"foo": Field(str)})))
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, Permissive)
    assert isinstance(recevied_config_type.fields["foo"].config_type, String)
    _dict_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_node_def_snaps_array():
    @op(config_schema=Field([str]))
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, Array)
    assert isinstance(recevied_config_type.inner_type, String)
    _array_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_node_def_snaps_map():
    @op(config_schema=Field({str: str}))
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, Map)
    assert isinstance(recevied_config_type.key_type, String)
    assert isinstance(recevied_config_type.inner_type, String)
    _map_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_node_def_snaps_map_with_name():
    @op(config_schema=Field(Map(bool, float, key_label_name="title")))
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, Map)
    assert isinstance(recevied_config_type.key_type, Bool)
    assert isinstance(recevied_config_type.inner_type, Float)
    assert recevied_config_type.given_name == "title"
    _map_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_node_def_snaps_noneable():
    @op(config_schema=Field(Noneable(str)))
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, Noneable)
    assert isinstance(recevied_config_type.inner_type, String)


def test_deserialize_node_def_snaps_multi_type_config(snapshot):
    @op(
        config_schema=Field(
            Permissive(
                {
                    "foo": Field(Array(float)),
                    "bar": Selector(
                        {
                            "baz": Field(Noneable(int)),
                            "qux": {
                                "quux": Field(str),
                                "corge": Field(
                                    Enum(
                                        "RGB",
                                        [
                                            EnumValue("red"),
                                            EnumValue("green"),
                                            EnumValue("blue"),
                                        ],
                                    )
                                ),
                            },
                        }
                    ),
                }
            )
        )
    )
    def fancy_op(_):
        pass

    @job
    def noop_job():
        fancy_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("fancy_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    snapshot.assert_match(serialize_pp(snap_from_config_type(recevied_config_type)))  # ty: ignore[invalid-argument-type]
    _dict_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


@pytest.mark.parametrize("dict_config_type", [Selector, Permissive, Shape])
def test_multi_type_config_array_dict_fields(dict_config_type, snapshot):
    @op(config_schema=Array(dict_config_type({"foo": Field(int), "bar": Field(str)})))
    def fancy_op(_):
        pass

    @job
    def noop_job():
        fancy_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("fancy_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    snapshot.assert_match(serialize_pp(snap_from_config_type(recevied_config_type)))  # ty: ignore[invalid-argument-type]
    _array_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_multi_type_config_array_map(snapshot):
    @op(config_schema=Array(Map(str, int)))
    def fancy_op(_):
        pass

    @job
    def noop_job():
        fancy_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("fancy_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    snapshot.assert_match(serialize_pp(snap_from_config_type(recevied_config_type)))  # ty: ignore[invalid-argument-type]
    _array_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


@pytest.mark.parametrize(
    "nested_dict_types",
    [combo for combo in itertools.permutations((Selector, Permissive, Shape), 3)],
)
def test_multi_type_config_nested_dicts(nested_dict_types, snapshot):
    D1, D2, D3 = nested_dict_types

    @op(config_schema=D1({"foo": D2({"bar": D3({"baz": Field(int)})})}))
    def fancy_op(_):
        pass

    @job
    def noop_job():
        fancy_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("fancy_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    snapshot.assert_match(serialize_pp(snap_from_config_type(recevied_config_type)))  # ty: ignore[invalid-argument-type]
    _dict_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )
