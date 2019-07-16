from collections import defaultdict, OrderedDict
import itertools

from dagster import check

from dagster.core.definitions import PipelineDefinition, Solid
from dagster.core.definitions.utils import DEFAULT_OUTPUT
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.execution.plan.objects import StepKind


class PipelineExecutionResult(object):
    '''Output of execution of the whole pipeline. Returned eg by :py:func:`execute_pipeline`.
    '''

    def __init__(self, pipeline, run_id, event_list, reconstruct_context):
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.run_id = check.str_param(run_id, 'run_id')
        self.event_list = check.list_param(event_list, 'step_event_list', of_type=DagsterEvent)
        self.reconstruct_context = check.callable_param(reconstruct_context, 'reconstruct_context')

        # Dict[string: solid_name, SolidExecutionResult]
        solid_result_dict = self._context_solid_result_dict(event_list)

        self.solid_result_dict = solid_result_dict
        self.solid_result_list = list(self.solid_result_dict.values())

    def _context_solid_result_dict(self, event_list):
        solid_set = set()
        solid_order = []
        step_events_by_solid_by_kind = defaultdict(lambda: defaultdict(list))
        step_event_list = [event for event in event_list if event.is_step_event]
        for step_event in step_event_list:
            solid_handle = step_event.solid_handle
            if solid_handle not in solid_set:
                solid_order.append(solid_handle)
                solid_set.add(solid_handle)

            step_events_by_solid_by_kind[solid_handle][step_event.step_kind].append(step_event)

        solid_result_dict = OrderedDict()

        for solid_handle in solid_order:
            solid_result_dict[solid_handle] = SolidExecutionResult(
                self.pipeline.get_solid(solid_handle),
                dict(step_events_by_solid_by_kind[solid_handle]),
                self.reconstruct_context,
            )
        return solid_result_dict

    @property
    def success(self):
        '''Whether the pipeline execution was successful at all steps'''
        return all([not event.is_failure for event in self.event_list])

    @property
    def step_event_list(self):
        '''The full list of step events'''
        return [event for event in self.event_list if event.is_step_event]

    def result_for_solid(self, name):
        '''Get a :py:class:`SolidExecutionResult` for a given top level solid name.
        '''
        check.str_param(name, 'name')

        if not self.pipeline.has_solid_named(name):
            raise DagsterInvariantViolationError(
                'Try to get result for solid {name} in {pipeline}. No such solid.'.format(
                    name=name, pipeline=self.pipeline.display_name
                )
            )
        top_level_results = {
            solid_id.name: result
            for solid_id, result in self.solid_result_dict.items()
            if solid_id.parent is None
        }
        if name not in top_level_results:
            raise DagsterInvariantViolationError(
                'Did not find result for solid {name} in pipeline execution result'.format(
                    name=name
                )
            )

        return top_level_results[name]

    def result_for_handle(self, handle):
        '''Get a :py:class:`SolidExecutionResult` for a given solid handle string.
        '''
        check.str_param(handle, 'handle')
        results = {
            solid_id.to_string(): result for solid_id, result in self.solid_result_dict.items()
        }

        if handle not in results:
            raise DagsterInvariantViolationError(
                (
                    'Did not find result for solid handle {handle} in pipeline execution result. '
                    'Available handles: {handles}'
                ).format(handle=handle, handles=list(results.keys()))
            )

        return results[handle]


class SolidExecutionResult(object):
    '''Execution result for one solid of the pipeline.
    '''

    def __init__(self, solid, step_events_by_kind, reconstruct_context):
        self.solid = check.inst_param(solid, 'solid', Solid)
        self.step_events_by_kind = check.dict_param(
            step_events_by_kind, 'step_events_by_kind', key_type=StepKind, value_type=list
        )
        self.reconstruct_context = check.callable_param(reconstruct_context, 'reconstruct_context')

    @property
    def compute_input_event_dict(self):
        '''input_events_during_compute keyed by input name'''
        return {se.event_specific_data.input_name: se for se in self.input_events_during_compute}

    @property
    def input_events_during_compute(self):
        '''All events of type STEP_INPUT'''
        return self._compute_steps_of_type(DagsterEventType.STEP_INPUT)

    @property
    def compute_output_event_dict(self):
        '''output_events_during_compute keyed by output name'''
        return {se.event_specific_data.output_name: se for se in self.output_events_during_compute}

    def get_output_event_for_compute(self, output_name='result'):
        '''The STEP_OUTPUT events for the given output name'''
        return self.compute_output_event_dict[output_name]

    @property
    def output_events_during_compute(self):
        '''All events of type STEP_OUTPUT'''
        return self._compute_steps_of_type(DagsterEventType.STEP_OUTPUT)

    @property
    def compute_step_events(self):
        '''All events that happen during the solid compute function'''
        return self.step_events_by_kind.get(StepKind.COMPUTE, [])

    @property
    def materializations_during_compute(self):
        '''The Materializations objects yielded by the solid'''
        return [
            mat_event.event_specific_data.materialization
            for mat_event in self.materialization_events_during_compute
        ]

    @property
    def materialization_events_during_compute(self):
        '''All events of type STEP_MATERIALIZATION'''
        return self._compute_steps_of_type(DagsterEventType.STEP_MATERIALIZATION)

    @property
    def expectation_events_during_compute(self):
        '''All events of type STEP_EXPECTATION_RESULT'''
        return self._compute_steps_of_type(DagsterEventType.STEP_EXPECTATION_RESULT)

    def _compute_steps_of_type(self, dagster_event_type):
        return list(
            filter(lambda se: se.event_type == dagster_event_type, self.compute_step_events)
        )

    @property
    def expectation_results_during_compute(self):
        '''The ExpectationResult objects yielded by the solid'''
        return [
            expt_event.event_specific_data.expectation_result
            for expt_event in self.expectation_events_during_compute
        ]

    def get_step_success_event(self):
        '''The STEP_SUCCESS event, throws if not present'''
        for step_event in self.compute_step_events:
            if step_event.event_type == DagsterEventType.STEP_SUCCESS:
                return step_event

        check.failed('Step success not found for solid {}'.format(self.solid.name))

    @property
    def input_expectation_step_events(self):
        '''All events of type INPUT_EXPECTATION'''
        return self.step_events_by_kind.get(StepKind.INPUT_EXPECTATION, [])

    @property
    def output_expectation_step_events(self):
        '''All events of type OUTPUT_EXPECTATION'''
        return self.step_events_by_kind.get(StepKind.OUTPUT_EXPECTATION, [])

    @property
    def compute_step_failure_event(self):
        '''The STEP_FAILURE event, throws if it did not fail'''
        if self.success:
            raise DagsterInvariantViolationError(
                'Cannot call compute_step_failure_event if successful'
            )

        step_failure_events = self._compute_steps_of_type(DagsterEventType.STEP_FAILURE)
        check.invariant(len(step_failure_events) == 1)
        return step_failure_events[0]

    @property
    def success(self):
        '''Whether the solid execution was successful'''
        any_success = False
        for step_event in itertools.chain(
            self.input_expectation_step_events,
            self.output_expectation_step_events,
            self.compute_step_events,
        ):
            if step_event.event_type == DagsterEventType.STEP_FAILURE:
                return False
            if step_event.event_type == DagsterEventType.STEP_SUCCESS:
                any_success = True

        return any_success

    @property
    def skipped(self):
        '''Whether the solid execution was skipped'''
        return all(
            [
                step_event.event_type == DagsterEventType.STEP_SKIPPED
                for step_event in itertools.chain(
                    self.input_expectation_step_events,
                    self.output_expectation_step_events,
                    self.compute_step_events,
                )
            ]
        )

    @property
    def output_values(self):
        '''Return dictionary of computed results, with keys being output names.
        Returns None if execution result isn't a success.

        Reconstructs the pipeline context to materialize values.
        '''
        if self.success and self.compute_step_events:
            with self.reconstruct_context() as context:
                values = {
                    compute_step_event.step_output_data.output_name: self._get_value(
                        context, compute_step_event.step_output_data
                    )
                    for compute_step_event in self.compute_step_events
                    if compute_step_event.is_successful_output
                }
            return values
        else:
            return None

    def output_value(self, output_name=DEFAULT_OUTPUT):
        '''Returns computed value either for DEFAULT_OUTPUT or for the output
        given as output_name. Returns None if execution result isn't a success.

        Reconstructs the pipeline context to materialize value.
        '''
        check.str_param(output_name, 'output_name')

        if not self.solid.definition.has_output(output_name):
            raise DagsterInvariantViolationError(
                '{output_name} not defined in solid {solid}'.format(
                    output_name=output_name, solid=self.solid.name
                )
            )

        if self.success:
            for compute_step_event in self.compute_step_events:
                if (
                    compute_step_event.is_successful_output
                    and compute_step_event.step_output_data.output_name == output_name
                ):
                    with self.reconstruct_context() as context:
                        value = self._get_value(context, compute_step_event.step_output_data)
                    return value

            raise DagsterInvariantViolationError(
                (
                    'Did not find result {output_name} in solid {self.solid.name} '
                    'execution result'
                ).format(output_name=output_name, self=self)
            )
        else:
            return None

    def _get_value(self, context, step_output_data):
        return context.intermediates_manager.get_intermediate(
            context=context,
            runtime_type=self.solid.output_def_named(step_output_data.output_name).runtime_type,
            step_output_handle=step_output_data.step_output_handle,
        )

    @property
    def failure_data(self):
        '''Returns the failing step's data that happened during this solid's execution, if any'''
        for step_event in itertools.chain(
            self.input_expectation_step_events,
            self.output_expectation_step_events,
            self.compute_step_events,
        ):
            if step_event.event_type == DagsterEventType.STEP_FAILURE:
                return step_event.step_failure_data
