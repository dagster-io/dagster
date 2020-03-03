import time

from dagster import check
from dagster.core.events import DagsterEvent
from dagster.core.execution.retries import Retries

from .plan import ExecutionPlan


def _default_sort_key(step):
    return int(step.tags.get('dagster/priority', 0)) * -1


class ActiveExecution(object):
    '''State machine used to track progress through execution of an ExecutionPlan
    '''

    def __init__(self, execution_plan, retries, sort_key_fn=None):
        self._plan = check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
        self._retries = check.inst_param(retries, 'retries', Retries)
        self._sort_key_fn = check.opt_callable_param(sort_key_fn, 'sort_key_fn', _default_sort_key)

        # All steps to be executed start out here in _pending
        self._pending = self._plan.execution_deps()

        # steps move in to these buckets as a result of _update calls
        self._executable = []
        self._pending_skip = []
        self._pending_retry = []
        self._waiting_to_retry = {}

        # then are considered _in_flight when vended via get_steps_to_*
        self._in_flight = set()

        # and finally their terminal state is tracked by these sets, via mark_*
        self._completed = set()
        self._success = set()
        self._failed = set()
        self._skipped = set()

        # Start the show by loading _executable with the set of _pending steps that have no deps
        self._update()

    def _update(self):
        '''Moves steps from _pending to _executable / _pending_skip / _pending_retry
           as a function of what has been _completed
        '''
        new_steps_to_execute = []
        new_steps_to_skip = []
        for step_key, requirements in self._pending.items():

            if requirements.issubset(self._completed):
                if requirements.issubset(self._success):
                    new_steps_to_execute.append(step_key)
                else:
                    new_steps_to_skip.append(step_key)

        for key in new_steps_to_execute:
            self._executable.append(key)
            del self._pending[key]

        for key in new_steps_to_skip:
            self._pending_skip.append(key)
            del self._pending[key]

        ready_to_retry = []
        tick_time = time.time()
        for key, at_time in self._waiting_to_retry.items():
            if tick_time >= at_time:
                ready_to_retry.append(key)

        for key in ready_to_retry:
            self._executable.append(key)
            del self._waiting_to_retry[key]

    def sleep_til_ready(self):
        now = time.time()
        sleep_amt = min([ready_at - now for ready_at in self._waiting_to_retry.values()])
        if sleep_amt > 0:
            time.sleep(sleep_amt)

    def get_next_step(self):
        check.invariant(not self.is_complete, 'Can not call get_next_step when is_complete is True')

        steps = self.get_steps_to_execute(limit=1)
        step = None

        if steps:
            step = steps[0]
        elif self._waiting_to_retry:
            self.sleep_til_ready()
            step = self.get_next_step()

        check.invariant(step is not None, 'Unexpected ActiveExecution state')
        return step

    def get_steps_to_execute(self, limit=None):
        check.opt_int_param(limit, 'limit')
        self._update()

        steps = sorted(
            [self._plan.get_step_by_key(key) for key in self._executable], key=self._sort_key_fn
        )

        if limit:
            steps = steps[:limit]

        for step in steps:
            self._in_flight.add(step.key)
            self._executable.remove(step.key)

        return steps

    def get_steps_to_skip(self):
        self._update()

        steps = []
        steps_to_skip = list(self._pending_skip)
        for key in steps_to_skip:
            steps.append(self._plan.get_step_by_key(key))
            self._in_flight.add(key)
            self._pending_skip.remove(key)

        return sorted(steps, key=self._sort_key_fn)

    def skipped_step_events_iterator(self, pipeline_context):
        '''Process all steps that can be skipped by repeated calls to get_steps_to_skip
        '''

        failed_or_skipped_steps = self._skipped.union(self._failed)

        steps_to_skip = self.get_steps_to_skip()
        while steps_to_skip:
            for step in steps_to_skip:
                step_context = pipeline_context.for_step(step)
                failed_inputs = []
                for step_input in step.step_inputs:
                    failed_inputs.extend(
                        failed_or_skipped_steps.intersection(step_input.dependency_keys)
                    )

                step_context.log.info(
                    'Dependencies for step {step} failed: {failed_inputs}. Not executing.'.format(
                        step=step.key, failed_inputs=failed_inputs
                    )
                )
                yield DagsterEvent.step_skipped_event(step_context)

                self.mark_skipped(step.key)

            steps_to_skip = self.get_steps_to_skip()

    def mark_failed(self, step_key):
        self._failed.add(step_key)
        self._mark_complete(step_key)

    def mark_success(self, step_key):
        self._success.add(step_key)
        self._mark_complete(step_key)

    def mark_skipped(self, step_key):
        self._skipped.add(step_key)
        self._mark_complete(step_key)

    def mark_up_for_retry(self, step_key, at_time=None):
        check.invariant(
            not self._retries.disabled,
            'Attempted to mark {} as up for retry but retries are disabled'.format(step_key),
        )
        check.opt_float_param(at_time, 'at_time')

        # if retries are enabled - queue this back up
        if self._retries.enabled:
            if at_time:
                self._waiting_to_retry[step_key] = at_time
            else:
                self._pending[step_key] = self._plan.execution_deps()[step_key]

        elif self._retries.deferred:
            self._completed.add(step_key)

        self._retries.mark_attempt(step_key)
        self._in_flight.remove(step_key)

    def _mark_complete(self, step_key):
        check.invariant(
            step_key not in self._completed,
            'Attempted to mark step {} as complete that was already completed'.format(step_key),
        )
        check.invariant(
            step_key in self._in_flight,
            'Attempted to mark step {} as complete that was not known to be in flight'.format(
                step_key
            ),
        )
        self._in_flight.remove(step_key)
        self._completed.add(step_key)

    def handle_event(self, dagster_event):
        check.inst_param(dagster_event, 'dagster_event', DagsterEvent)

        if dagster_event.is_step_failure:
            self.mark_failed(dagster_event.step_key)
        elif dagster_event.is_step_success:
            self.mark_success(dagster_event.step_key)
        elif dagster_event.is_step_up_for_retry:
            self.mark_up_for_retry(
                dagster_event.step_key,
                time.time() + dagster_event.step_retry_data.seconds_to_wait
                if dagster_event.step_retry_data.seconds_to_wait
                else None,
            )

    def verify_complete(self, pipeline_context, step_key):
        '''Ensure that a step has reached a terminal state, if it has not mark it as an unexpected failure
        '''
        if step_key in self._in_flight:
            pipeline_context.log.error(
                'Step {key} finished without success or failure event, assuming failure.'.format(
                    key=step_key
                )
            )
            self.mark_failed(step_key)

    @property
    def is_complete(self):
        return (
            len(self._pending) == 0
            and len(self._in_flight) == 0
            and len(self._executable) == 0
            and len(self._pending_skip) == 0
            and len(self._pending_retry) == 0
            and len(self._waiting_to_retry) == 0
        )
