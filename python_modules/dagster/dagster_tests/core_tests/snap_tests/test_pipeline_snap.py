from dagster import InputDefinition, Nothing, OutputDefinition, pipeline, solid
from dagster.core.snap.dep_snapshot import (
    DependencyStructureIndex,
    InputHandle,
    OutputHandleSnap,
    SolidInvocationSnap,
    build_dep_structure_snapshot_from_icontains_solids,
)
from dagster.core.snap.pipeline_snapshot import PipelineSnapshot, create_pipeline_snapshot_id
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple


def serialize_rt(value):
    return deserialize_json_to_dagster_namedtuple(serialize_dagster_namedtuple(value))


def serialize_pp(value):
    return serialize_dagster_namedtuple(value, indent=2, separators=(',', ': '))


def get_noop_pipeline():
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    return noop_pipeline


def test_empty_pipeline_snap_snapshot(snapshot):
    snapshot.assert_match(serialize_pp(PipelineSnapshot.from_pipeline_def(get_noop_pipeline())))


def test_empty_pipeline_snap_props(snapshot):

    pipeline_snapshot = PipelineSnapshot.from_pipeline_def(get_noop_pipeline())

    assert pipeline_snapshot.name == 'noop_pipeline'
    assert pipeline_snapshot.description is None
    assert pipeline_snapshot.tags == {}

    assert pipeline_snapshot == serialize_rt(pipeline_snapshot)

    snapshot.assert_match(serialize_pp(pipeline_snapshot))
    snapshot.assert_match(create_pipeline_snapshot_id(pipeline_snapshot))


def test_pipeline_snap_all_props(snapshot):
    @solid
    def noop_solid(_):
        pass

    @pipeline(description='desc', tags={'key': 'value'})
    def noop_pipeline():
        noop_solid()

    pipeline_snapshot = PipelineSnapshot.from_pipeline_def(noop_pipeline)

    assert pipeline_snapshot.name == 'noop_pipeline'
    assert pipeline_snapshot.description == 'desc'
    assert pipeline_snapshot.tags == {'key': 'value'}

    assert pipeline_snapshot == serialize_rt(pipeline_snapshot)

    snapshot.assert_match(serialize_pp(pipeline_snapshot))
    snapshot.assert_match(create_pipeline_snapshot_id(pipeline_snapshot))


def test_noop_deps_snap():
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    invocations = build_dep_structure_snapshot_from_icontains_solids(
        noop_pipeline
    ).solid_invocation_snaps
    assert len(invocations) == 1
    assert isinstance(invocations[0], SolidInvocationSnap)


def test_two_invocations_deps_snap(snapshot):
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def two_solid_pipeline():
        noop_solid.alias('one')()
        noop_solid.alias('two')()

    index = DependencyStructureIndex(
        build_dep_structure_snapshot_from_icontains_solids(two_solid_pipeline)
    )
    assert index.get_invocation('one')
    assert index.get_invocation('two')

    pipeline_snapshot = PipelineSnapshot.from_pipeline_def(two_solid_pipeline)
    assert pipeline_snapshot == serialize_rt(pipeline_snapshot)

    snapshot.assert_match(serialize_pp(pipeline_snapshot))
    snapshot.assert_match(create_pipeline_snapshot_id(pipeline_snapshot))


def test_basic_dep():
    @solid
    def return_one(_):
        return 1

    @solid(input_defs=[InputDefinition('value', int)])
    def passthrough(_, value):
        return value

    @pipeline
    def single_dep_pipeline():
        passthrough(return_one())

    index = DependencyStructureIndex(
        build_dep_structure_snapshot_from_icontains_solids(single_dep_pipeline)
    )

    assert index.get_invocation('return_one')
    assert index.get_invocation('passthrough')

    outputs = index.get_upstream_outputs('passthrough', 'value')
    assert len(outputs) == 1
    assert outputs[0].solid_name == 'return_one'
    assert outputs[0].output_name == 'result'


def test_basic_dep_fan_out(snapshot):
    @solid
    def return_one(_):
        return 1

    @solid(input_defs=[InputDefinition('value', int)])
    def passthrough(_, value):
        return value

    @pipeline
    def single_dep_pipeline():
        return_one_result = return_one()
        passthrough.alias('passone')(return_one_result)
        passthrough.alias('passtwo')(return_one_result)

    dep_structure_snapshot = build_dep_structure_snapshot_from_icontains_solids(single_dep_pipeline)
    index = DependencyStructureIndex(dep_structure_snapshot)

    assert index.get_invocation('return_one')
    assert index.get_invocation('passone')
    assert index.get_invocation('passtwo')

    assert index.get_upstream_output('passone', 'value') == OutputHandleSnap('return_one', 'result')
    assert index.get_upstream_output('passtwo', 'value') == OutputHandleSnap('return_one', 'result')

    assert set(index.get_downstream_inputs('return_one', 'result')) == set(
        [
            InputHandle('passthrough', 'passone', 'value'),
            InputHandle('passthrough', 'passtwo', 'value'),
        ]
    )

    assert (
        deserialize_json_to_dagster_namedtuple(serialize_dagster_namedtuple(dep_structure_snapshot))
        == dep_structure_snapshot
    )

    pipeline_snapshot = PipelineSnapshot.from_pipeline_def(single_dep_pipeline)
    assert pipeline_snapshot == serialize_rt(pipeline_snapshot)

    snapshot.assert_match(serialize_pp(pipeline_snapshot))
    snapshot.assert_match(create_pipeline_snapshot_id(pipeline_snapshot))


def test_basic_fan_in(snapshot):
    @solid(output_defs=[OutputDefinition(Nothing)])
    def return_nothing(_):
        return None

    @solid(input_defs=[InputDefinition('nothing', Nothing)])
    def take_nothings(_):
        return None

    @pipeline
    def fan_in_test():
        take_nothings(
            [return_nothing.alias('nothing_one')(), return_nothing.alias('nothing_two')()]
        )

    dep_structure_snapshot = build_dep_structure_snapshot_from_icontains_solids(fan_in_test)
    index = DependencyStructureIndex(dep_structure_snapshot)

    assert index.get_invocation('nothing_one')
    assert index.get_invocation('take_nothings')

    assert index.get_upstream_outputs('take_nothings', 'nothing') == [
        OutputHandleSnap('nothing_one', 'result'),
        OutputHandleSnap('nothing_two', 'result'),
    ]

    assert (
        deserialize_json_to_dagster_namedtuple(serialize_dagster_namedtuple(dep_structure_snapshot))
        == dep_structure_snapshot
    )

    pipeline_snapshot = PipelineSnapshot.from_pipeline_def(fan_in_test)
    assert pipeline_snapshot == serialize_rt(pipeline_snapshot)

    snapshot.assert_match(serialize_pp(pipeline_snapshot))
    snapshot.assert_match(create_pipeline_snapshot_id(pipeline_snapshot))
