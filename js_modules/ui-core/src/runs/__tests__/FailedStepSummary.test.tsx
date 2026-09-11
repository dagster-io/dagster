import {
  buildExecutionStepFailureEvent,
  buildPythonError,
  buildResourceInitFailureEvent,
  buildRunFailureEvent,
} from '../../graphql/builders';
import {summarizeFailure} from '../FailedStepSummary';
import {LogsProviderLogs} from '../LogsProvider';
import {EMPTY_RUN_METADATA, IRunMetadataDict, IStepState} from '../RunMetadataProvider';
import {LogNode} from '../types';

const asNode = (event: object): LogNode => ({...event, clientsideKey: 'k'}) as unknown as LogNode;

const logsOf = (nodes: LogNode[]): LogsProviderLogs =>
  ({allNodeChunks: [nodes], counts: {}, loading: false}) as unknown as LogsProviderLogs;

const failedStep = (end: number) => ({
  state: IStepState.FAILED,
  end,
  transitions: [],
  attempts: [],
  markers: [],
});

const metadataWithFailedSteps = (steps: Record<string, number>): IRunMetadataDict => ({
  ...EMPTY_RUN_METADATA,
  steps: Object.fromEntries(Object.entries(steps).map(([key, end]) => [key, failedStep(end)])),
});

describe('summarizeFailure', () => {
  it('uses the ExecutionStepFailureEvent for the earliest failed step', () => {
    const logs = logsOf([
      asNode(
        buildExecutionStepFailureEvent({
          stepKey: 'first',
          error: buildPythonError({message: 'boom'}),
        }),
      ),
      asNode(
        buildExecutionStepFailureEvent({
          stepKey: 'second',
          error: buildPythonError({message: 'later'}),
        }),
      ),
    ]);
    const summary = summarizeFailure(logs, metadataWithFailedSteps({second: 20, first: 10}));

    expect(summary?.stepKey).toBe('first');
    expect(summary?.message).toBe('boom');
    expect(summary?.otherFailedCount).toBe(1);
    expect(summary?.failureNode?.__typename).toBe('ExecutionStepFailureEvent');
  });

  it('uses the ResourceInitFailureEvent when a resource failed to initialize', () => {
    const logs = logsOf([
      asNode(
        buildResourceInitFailureEvent({
          stepKey: 'needs_db',
          error: buildPythonError({message: 'could not connect'}),
        }),
      ),
    ]);
    const summary = summarizeFailure(logs, metadataWithFailedSteps({needs_db: 10}));

    expect(summary?.stepKey).toBe('needs_db');
    expect(summary?.message).toBe('could not connect');
    expect(summary?.failureNode?.__typename).toBe('ResourceInitFailureEvent');
  });

  it('falls back to the event message when there is no python error', () => {
    const logs = logsOf([
      asNode(
        buildResourceInitFailureEvent({stepKey: 'needs_db', error: null, message: 'init failed'}),
      ),
    ]);
    const summary = summarizeFailure(logs, metadataWithFailedSteps({needs_db: 10}));

    expect(summary?.message).toBe('init failed');
  });

  it('reports a failed step without details when its failure event is not loaded', () => {
    const summary = summarizeFailure(logsOf([]), metadataWithFailedSteps({missing: 10}));

    expect(summary?.stepKey).toBe('missing');
    expect(summary?.message).toBeNull();
    expect(summary?.failureNode).toBeNull();
  });

  it('summarizes a run-level failure when no step failed', () => {
    const logs = logsOf([
      asNode(buildRunFailureEvent({error: buildPythonError({message: 'run blew up'})})),
    ]);
    const summary = summarizeFailure(logs, EMPTY_RUN_METADATA);

    expect(summary?.stepKey).toBeNull();
    expect(summary?.message).toBe('run blew up');
    expect(summary?.failureNode).toBeNull();
  });

  it('returns null when nothing failed', () => {
    expect(summarizeFailure(logsOf([]), EMPTY_RUN_METADATA)).toBeNull();
  });
});
