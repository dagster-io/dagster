import itertools

import dagster as dg
import pytest
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
from dagster._serdes import serialize_pp


def serialize_rt(value: JobSnap) -> JobSnap:
    return dg.deserialize_value(dg.serialize_value(value), JobSnap)


def get_noop_pipeline():
    @dg.op
    def noop_op(_):
        pass

    @dg.job
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
    @dg.op
    def noop_op(_):
        pass

    @dg.job(description="desc", tags={"key": "value"})
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
    @dg.op
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    invocations = build_dep_structure_snapshot_from_graph_def(noop_job.graph).node_invocation_snaps
    assert len(invocations) == 1
    assert isinstance(invocations[0], NodeInvocationSnap)


def test_two_invocations_deps_snap(snapshot):
    @dg.op
    def noop_op(_):
        pass

    @dg.job
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
    @dg.op
    def return_one(_):
        return 1

    @dg.op(ins={"value": dg.In(int)})
    def passthrough(_, value):
        return value

    @dg.job
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
    @dg.op
    def return_one(_):
        return 1

    @dg.op(ins={"value": dg.In(int)})
    def passthrough(_, value):
        return value

    @dg.job
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
        dg.deserialize_value(
            dg.serialize_value(dep_structure_snapshot), DependencyStructureSnapshot
        )
        == dep_structure_snapshot
    )

    job_snapshot = JobSnap.from_job_def(single_dep_job)
    assert job_snapshot == serialize_rt(job_snapshot)

    snapshot.assert_match(serialize_pp(job_snapshot))
    snapshot.assert_match(job_snapshot.snapshot_id)


def test_basic_fan_in(snapshot):
    @dg.op(out=dg.Out(dg.Nothing))
    def return_nothing(_):
        return None

    @dg.op(ins={"nothing": dg.In(dg.Nothing)})
    def take_nothings(_):
        return None

    @dg.job
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
        dg.deserialize_value(
            dg.serialize_value(dep_structure_snapshot), DependencyStructureSnapshot
        )
        == dep_structure_snapshot
    )

    job_snapshot = JobSnap.from_job_def(fan_in_test)
    assert job_snapshot == serialize_rt(job_snapshot)

    snapshot.assert_match(serialize_pp(job_snapshot))
    snapshot.assert_match(job_snapshot.snapshot_id)


def _dict_has_stable_hashes(hydrated_map, snapshot_config_snap_map):
    assert isinstance(hydrated_map, (dg.Shape, dg.Permissive, dg.Selector))
    assert hydrated_map.key in snapshot_config_snap_map
    for field in hydrated_map.fields.values():
        assert field.config_type.key in snapshot_config_snap_map


def _array_has_stable_hashes(hydrated_array, snapshot_config_snap_map):
    assert isinstance(hydrated_array, dg.Array)
    assert hydrated_array.key in snapshot_config_snap_map
    assert hydrated_array.inner_type.key in snapshot_config_snap_map


def _map_has_stable_hashes(hydrated_map, snapshot_config_snap_map):
    assert isinstance(hydrated_map, dg.Map)
    assert hydrated_map.key in snapshot_config_snap_map
    assert hydrated_map.inner_type.key in snapshot_config_snap_map
    assert hydrated_map.key_type.key in snapshot_config_snap_map


def test_deserialize_op_def_snaps_default_field():
    @dg.op(
        config_schema={
            "foo": dg.Field(str, is_required=False, default_value="hello"),
            "bar": dg.Field(str),
        }
    )
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, dg.Shape)
    assert isinstance(recevied_config_type.fields["foo"].config_type, dg.String)
    assert isinstance(recevied_config_type.fields["bar"].config_type, dg.String)
    assert not recevied_config_type.fields["foo"].is_required
    assert recevied_config_type.fields["foo"].default_value == "hello"
    _dict_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_node_def_snaps_enum():
    @dg.op(
        config_schema=dg.Field(
            dg.Enum("CowboyType", [dg.EnumValue("good"), dg.EnumValue("bad"), dg.EnumValue("ugly")])
        )
    )
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, dg.Enum)
    assert recevied_config_type.given_name == "CowboyType"
    assert all(
        enum_value.config_value in ("good", "bad", "ugly")
        for enum_value in recevied_config_type.enum_values
    )


def test_deserialize_node_def_snaps_strict_shape():
    @dg.op(config_schema={"foo": dg.Field(str, is_required=False), "bar": dg.Field(str)})
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, dg.Shape)
    assert isinstance(recevied_config_type.fields["foo"].config_type, dg.String)
    assert isinstance(recevied_config_type.fields["bar"].config_type, dg.String)
    assert not recevied_config_type.fields["foo"].is_required
    _dict_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_node_def_snaps_selector():
    @dg.op(config_schema=dg.Selector({"foo": dg.Field(str), "bar": dg.Field(int)}))
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, dg.Selector)
    assert isinstance(recevied_config_type.fields["foo"].config_type, dg.String)
    assert isinstance(recevied_config_type.fields["bar"].config_type, dg.Int)
    _dict_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_op_def_snaps_permissive():
    @dg.op(config_schema=dg.Field(dg.Permissive({"foo": dg.Field(str)})))
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, dg.Permissive)
    assert isinstance(recevied_config_type.fields["foo"].config_type, dg.String)
    _dict_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_node_def_snaps_array():
    @dg.op(config_schema=dg.Field([str]))
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, dg.Array)
    assert isinstance(recevied_config_type.inner_type, dg.String)
    _array_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_node_def_snaps_map():
    @dg.op(config_schema=dg.Field({str: str}))
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, dg.Map)
    assert isinstance(recevied_config_type.key_type, dg.String)
    assert isinstance(recevied_config_type.inner_type, dg.String)
    _map_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_node_def_snaps_map_with_name():
    @dg.op(config_schema=dg.Field(dg.Map(bool, float, key_label_name="title")))
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, dg.Map)
    assert isinstance(recevied_config_type.key_type, dg.Bool)
    assert isinstance(recevied_config_type.inner_type, dg.Float)
    assert recevied_config_type.given_name == "title"
    _map_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_deserialize_node_def_snaps_noneable():
    @dg.op(config_schema=dg.Field(dg.Noneable(str)))
    def noop_op(_):
        pass

    @dg.job
    def noop_job():
        noop_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("noop_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    assert isinstance(recevied_config_type, dg.Noneable)
    assert isinstance(recevied_config_type.inner_type, dg.String)


def test_deserialize_node_def_snaps_multi_type_config(snapshot):
    @dg.op(
        config_schema=dg.Field(
            dg.Permissive(
                {
                    "foo": dg.Field(dg.Array(float)),
                    "bar": dg.Selector(
                        {
                            "baz": dg.Field(dg.Noneable(int)),
                            "qux": {
                                "quux": dg.Field(str),
                                "corge": dg.Field(
                                    dg.Enum(
                                        "RGB",
                                        [
                                            dg.EnumValue("red"),
                                            dg.EnumValue("green"),
                                            dg.EnumValue("blue"),
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

    @dg.job
    def noop_job():
        fancy_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("fancy_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    snapshot.assert_match(serialize_pp(snap_from_config_type(recevied_config_type)))  # pyright: ignore[reportArgumentType]
    _dict_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


@pytest.mark.parametrize("dict_config_type", [dg.Selector, dg.Permissive, dg.Shape])
def test_multi_type_config_array_dict_fields(dict_config_type, snapshot):
    @dg.op(config_schema=dg.Array(dict_config_type({"foo": dg.Field(int), "bar": dg.Field(str)})))
    def fancy_op(_):
        pass

    @dg.job
    def noop_job():
        fancy_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("fancy_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    snapshot.assert_match(serialize_pp(snap_from_config_type(recevied_config_type)))  # pyright: ignore[reportArgumentType]
    _array_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


def test_multi_type_config_array_map(snapshot):
    @dg.op(config_schema=dg.Array(dg.Map(str, int)))
    def fancy_op(_):
        pass

    @dg.job
    def noop_job():
        fancy_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("fancy_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    snapshot.assert_match(serialize_pp(snap_from_config_type(recevied_config_type)))  # pyright: ignore[reportArgumentType]
    _array_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )


@pytest.mark.parametrize(
    "nested_dict_types",
    [combo for combo in itertools.permutations((dg.Selector, dg.Permissive, dg.Shape), 3)],
)
def test_multi_type_config_nested_dicts(nested_dict_types, snapshot):
    D1, D2, D3 = nested_dict_types

    @dg.op(config_schema=D1({"foo": D2({"bar": D3({"baz": dg.Field(int)})})}))
    def fancy_op(_):
        pass

    @dg.job
    def noop_job():
        fancy_op()

    job_snapshot = JobSnap.from_job_def(noop_job)
    node_def_snap = job_snapshot.get_node_def_snap("fancy_op")
    recevied_config_type = job_snapshot.get_config_type_from_node_def_snap(node_def_snap)
    snapshot.assert_match(serialize_pp(snap_from_config_type(recevied_config_type)))  # pyright: ignore[reportArgumentType]
    _dict_has_stable_hashes(
        recevied_config_type,
        job_snapshot.config_schema_snapshot.all_config_snaps_by_key,
    )
