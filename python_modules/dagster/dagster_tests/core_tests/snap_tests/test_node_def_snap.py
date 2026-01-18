import dagster as dg
from dagster._core.snap import DependencyStructureIndex, GraphDefSnap, build_graph_def_snap
from dagster._core.snap.node import OpDefSnap, build_node_defs_snapshot, build_op_def_snap


def test_basic_op_definition():
    @dg.op
    def noop_op(_):
        pass

    @dg.job
    def my_job():
        noop_op()

    op_snap = build_op_def_snap(noop_op, my_job)

    assert op_snap
    assert dg.deserialize_value(dg.serialize_value(op_snap), OpDefSnap) == op_snap


def test_op_definition_kitchen_sink():
    @dg.op(
        ins={"arg_one": dg.In(str, description="desc1"), "arg_two": dg.In(int)},
        out={
            "output_one": dg.Out(dagster_type=str),
            "output_two": dg.Out(
                dagster_type=int,
                description="desc2",
                is_required=False,
            ),
        },
        config_schema={"foo": int},
        description="a description",
        tags={"a_tag": "yup"},
        required_resource_keys={"b_resource", "a_resource"},
    )
    def kitchen_sink_op(_, arg_two, arg_one):  # out of order to test positional_inputs
        assert arg_one
        assert arg_two
        raise Exception("should not execute")

    @dg.job
    def my_job():
        kitchen_sink_op()

    kitchen_sink_op_snap = build_op_def_snap(kitchen_sink_op, my_job)

    assert kitchen_sink_op_snap
    assert kitchen_sink_op_snap.name == "kitchen_sink_op"
    assert len(kitchen_sink_op_snap.input_def_snaps) == 2
    assert [inp.name for inp in kitchen_sink_op_snap.input_def_snaps] == [
        "arg_one",
        "arg_two",
    ]
    assert [inp.dagster_type_key for inp in kitchen_sink_op_snap.input_def_snaps] == [
        "String",
        "Int",
    ]

    assert kitchen_sink_op_snap.get_input_snap("arg_one").description == "desc1"

    assert [out.name for out in kitchen_sink_op_snap.output_def_snaps] == [
        "output_one",
        "output_two",
    ]

    assert [out.dagster_type_key for out in kitchen_sink_op_snap.output_def_snaps] == [
        "String",
        "Int",
    ]

    assert kitchen_sink_op_snap.get_output_snap("output_two").description == "desc2"
    assert kitchen_sink_op_snap.get_output_snap("output_two").is_required is False

    assert kitchen_sink_op_snap.required_resource_keys == [
        "a_resource",
        "b_resource",
    ]
    assert kitchen_sink_op_snap.tags == {"a_tag": "yup"}
    assert kitchen_sink_op.positional_inputs == ["arg_two", "arg_one"]

    assert (
        dg.deserialize_value(dg.serialize_value(kitchen_sink_op_snap), OpDefSnap)
        == kitchen_sink_op_snap
    )


def test_noop_graph_definition():
    @dg.op
    def noop_op(_):
        pass

    @dg.graph
    def comp_graph():
        noop_op()

    comp_solid_meta = build_graph_def_snap(comp_graph, comp_graph.to_job())

    assert isinstance(comp_solid_meta, GraphDefSnap)
    assert (
        dg.deserialize_value(dg.serialize_value(comp_solid_meta), GraphDefSnap) == comp_solid_meta
    )


def test_basic_graph_definition():
    @dg.op
    def return_one(_):
        return 1

    @dg.op
    def take_one(_, one):
        return one

    @dg.graph
    def comp_graph():
        take_one(return_one())

    comp_solid_meta = build_graph_def_snap(comp_graph, comp_graph.to_job())

    assert isinstance(comp_solid_meta, GraphDefSnap)
    assert (
        dg.deserialize_value(dg.serialize_value(comp_solid_meta), GraphDefSnap) == comp_solid_meta
    )

    index = DependencyStructureIndex(comp_solid_meta.dep_structure_snapshot)
    assert index.get_invocation("return_one")
    assert index.get_invocation("take_one")
    assert index.get_upstream_output("take_one", "one").node_name == "return_one"
    assert index.get_upstream_output("take_one", "one").output_name == "result"


def test_complex_graph_definition():
    @dg.op
    def return_one(_):
        return 1

    @dg.op
    def take_many(_, items):
        return items

    @dg.graph
    def comp_graph(this_number):
        take_many([return_one(), this_number, return_one.alias("return_one_also")()])

    comp_solid_meta = build_graph_def_snap(comp_graph, comp_graph.to_job())

    assert isinstance(comp_solid_meta, GraphDefSnap)
    assert (
        dg.deserialize_value(dg.serialize_value(comp_solid_meta), GraphDefSnap) == comp_solid_meta
    )

    index = DependencyStructureIndex(comp_solid_meta.dep_structure_snapshot)
    assert index.get_invocation("return_one")
    assert index.get_invocation("take_many")
    assert index.get_upstream_outputs("take_many", "items")[0].node_name == "return_one"
    assert index.get_upstream_outputs("take_many", "items")[1].node_name == "return_one_also"


def test_asset_job_omits_output_description_and_metadata():
    @dg.asset(description="my description", metadata={"foo": "bar"})
    def my_asset():
        return 1

    @dg.asset
    def my_other_asset(my_asset):
        return my_asset + 1

    # Test with define_asset_job
    asset_job = dg.define_asset_job("my_asset_job", selection=[my_asset, my_other_asset])
    defs = dg.Definitions(assets=[my_asset, my_other_asset], jobs=[asset_job])
    job_def = defs.get_job_def("my_asset_job")

    assert job_def.is_asset_job

    # Build snapshots and find the my_asset op snap
    node_defs_snapshot = build_node_defs_snapshot(job_def)
    my_asset_op_snap = next(s for s in node_defs_snapshot.op_def_snaps if s.name == "my_asset")
    output_snap = my_asset_op_snap.get_output_snap("result")

    assert output_snap.description is None
    assert output_snap.metadata == {}

    # Test with implicit global asset job from Definitions
    defs_implicit = dg.Definitions(assets=[my_asset, my_other_asset])
    implicit_job = defs_implicit.get_implicit_global_asset_job_def()

    assert implicit_job.is_asset_job

    node_defs_snapshot_implicit = build_node_defs_snapshot(implicit_job)
    my_asset_op_snap_implicit = next(
        s for s in node_defs_snapshot_implicit.op_def_snaps if s.name == "my_asset"
    )
    output_snap_implicit = my_asset_op_snap_implicit.get_output_snap("result")

    assert output_snap_implicit.description is None
    assert output_snap_implicit.metadata == {}

    # Test with graph_asset - verifies build_graph_def_snap also strips metadata
    @dg.op
    def inner_op():
        return 1

    @dg.graph_asset(description="graph asset description", metadata={"graph_key": "graph_value"})
    def my_graph_asset():
        return inner_op()

    defs_with_graph = dg.Definitions(assets=[my_graph_asset])
    graph_asset_job = defs_with_graph.get_implicit_global_asset_job_def()

    assert graph_asset_job.is_asset_job

    node_defs_snapshot_graph = build_node_defs_snapshot(graph_asset_job)
    # Graph assets create a GraphDefSnap, not an OpDefSnap
    my_graph_asset_snap = next(
        s for s in node_defs_snapshot_graph.graph_def_snaps if s.name == "my_graph_asset"
    )
    graph_output_snap = my_graph_asset_snap.get_output_snap("result")

    assert graph_output_snap.description is None
    assert graph_output_snap.metadata == {}

    # Verify that non-asset jobs still include description and metadata
    @dg.op(out=dg.Out(description="op description", metadata={"key": "value"}))
    def my_op():
        return 1

    @dg.job
    def my_regular_job():
        my_op()

    assert not my_regular_job.is_asset_job

    my_op_snap = build_op_def_snap(my_op, my_regular_job)
    regular_output_snap = my_op_snap.get_output_snap("result")

    assert regular_output_snap.description == "op description"
    assert regular_output_snap.metadata == {"key": dg.TextMetadataValue("value")}
