from collections import defaultdict, OrderedDict
import itertools

from dagster import check

from dagster.core.definitions import PipelineDefinition, Solid
from dagster.core.definitions.utils import DEFAULT_OUTPUT
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.execution_plan.objects import StepKind


class PipelineExecutionResult(object):
    '''Result of execution of the whole pipeline. Returned eg by :py:func:`execute_pipeline`.
    '''

    def __init__(self, pipeline, run_id, event_list, reconstruct_context):
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.run_id = check.str_param(run_id, 'run_id')
        self.event_list = check.list_param(event_list, 'step_event_list', of_type=DagsterEvent)
        self.reconstruct_context = check.callable_param(reconstruct_context, 'reconstruct_context')

        solid_result_dict = self._context_solid_result_dict(event_list)

        self.solid_result_dict = solid_result_dict
        self.solid_result_list = list(self.solid_result_dict.values())

    def _context_solid_result_dict(self, event_list):
        solid_set = set()
        solid_order = []
        step_events_by_solid_by_kind = defaultdict(lambda: defaultdict(list))
        step_event_list = [event for event in event_list if event.is_step_event]
        for step_event in step_event_list:
            solid_name = step_event.solid_name
            if solid_name not in solid_set:
                solid_order.append(solid_name)
                solid_set.add(solid_name)

            step_events_by_solid_by_kind[solid_name][step_event.step_kind].append(step_event)

        solid_result_dict = OrderedDict()

        for solid_name in solid_order:
            solid_result_dict[solid_name] = SolidExecutionResult(
                self.pipeline.solid_named(solid_name),
                dict(step_events_by_solid_by_kind[solid_name]),
                self.reconstruct_context,
            )
        return solid_result_dict

    @property
    def success(self):
        '''Whether the pipeline execution was successful at all steps'''
        return all([not event.is_failure for event in self.event_list])

    @property
    def step_event_list(self):
        return [event for event in self.event_list if event.is_step_event]

    def result_for_solid(self, name):
        '''Get a :py:class:`SolidExecutionResult` for a given solid name.
        '''
        check.str_param(name, 'name')

        if not self.pipeline.has_solid_named(name):
            raise DagsterInvariantViolationError(
                'Try to get result for solid {name} in {pipeline}. No such solid.'.format(
                    name=name, pipeline=self.pipeline.display_name
                )
            )

        if name not in self.solid_result_dict:
            raise DagsterInvariantViolationError(
                'Did not find result for solid {name} in pipeline execution result'.format(
                    name=name
                )
            )

        return self.solid_result_dict[name]


class SolidExecutionResult(object):
    '''Execution result for one solid of the pipeline.

    Attributes:
      context (ExecutionContext): ExecutionContext of that particular Pipeline run.
      solid (SolidDefinition): Solid for which this result is
    '''

    def __init__(self, solid, step_events_by_kind, reconstruct_context):
        self.solid = check.inst_param(solid, 'solid', Solid)
        self.step_events_by_kind = check.dict_param(
            step_events_by_kind, 'step_events_by_kind', key_type=StepKind, value_type=list
        )
        self.reconstruct_context = check.callable_param(reconstruct_context, 'reconstruct_context')

    @property
    def transform(self):
        check.invariant(len(self.step_events_by_kind[StepKind.TRANSFORM]) == 1)
        return self.step_events_by_kind[StepKind.TRANSFORM][0]

    @property
    def transforms(self):
        return self.step_events_by_kind.get(StepKind.TRANSFORM, [])

    @property
    def input_expectations(self):
        return self.step_events_by_kind.get(StepKind.INPUT_EXPECTATION, [])

    @property
    def output_expectations(self):
        return self.step_events_by_kind.get(StepKind.OUTPUT_EXPECTATION, [])

    @property
    def success(self):
        '''Whether the solid execution was successful'''
        any_success = False
        for step_event in itertools.chain(
            self.input_expectations, self.output_expectations, self.transforms
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
                    self.input_expectations, self.output_expectations, self.transforms
                )
            ]
        )

    @property
    def transformed_values(self):
        '''Return dictionary of transformed results, with keys being output names.
        Returns None if execution result isn't a success.

        Reconstructs the pipeline context to materialize values.
        '''
        if self.success and self.transforms:
            with self.reconstruct_context() as context:
                values = {
                    result.step_output_data.output_name: self._get_value(
                        context, result.step_output_data
                    )
                    for result in self.transforms
                    if result.is_successful_output
                }
            return values
        else:
            return None

    def transformed_value(self, output_name=DEFAULT_OUTPUT):
        '''Returns transformed value either for DEFAULT_OUTPUT or for the output
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
            for result in self.transforms:
                if (
                    result.is_successful_output
                    and result.step_output_data.output_name == output_name
                ):
                    with self.reconstruct_context() as context:
                        value = self._get_value(context, result.step_output_data)
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
        for result in itertools.chain(
            self.input_expectations, self.output_expectations, self.transforms
        ):
            if result.event_type == DagsterEventType.STEP_FAILURE:
                return result.step_failure_data
