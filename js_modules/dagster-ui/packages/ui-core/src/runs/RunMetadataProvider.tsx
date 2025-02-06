import * as React from 'react';
import {useMemo} from 'react';

import {LogsProviderLogs} from './LogsProvider';
import {RunContext} from './RunContext';
import {gql, useQuery} from '../apollo-client';
import {flattenOneLevel} from '../util/flattenOneLevel';
import {RunFragment} from './types/RunFragments.types';
import {
  RunMetadataProviderMessageFragment,
  RunStepStatsFragment,
  RunStepStatsQuery,
  RunStepStatsQueryVariables,
} from './types/RunMetadataProvider.types';
import {StepEventStatus} from '../graphql/types';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntryFragment';

export enum IStepState {
  PREPARING = 'preparing',
  RETRY_REQUESTED = 'retry-requested',
  RUNNING = 'running',
  SUCCEEDED = 'succeeded',
  SKIPPED = 'skipped',
  FAILED = 'failed',
  UNKNOWN = 'unknown', // run exited without step reaching a final state
}

const BOX_EXIT_STATES = [
  IStepState.RETRY_REQUESTED,
  IStepState.SUCCEEDED,
  IStepState.FAILED,
  IStepState.UNKNOWN,
];

interface IMarker {
  key: string;
  start?: number;
  end?: number;
}

export interface IStepAttempt {
  start: number;
  end?: number;
  exitState?: IStepState;
}

export interface IStepMetadata {
  // current state
  state?: IStepState;

  // execution start and stop (user-code) inclusive of all retries
  start?: number;
  end?: number;

  // current state + prev state transition times
  transitions: {
    state: IStepState;
    time: number;
  }[];

  // transition times organized into start+stop+exit state pairs.
  // This is the metadata used to render boxes on the realtime vi.z
  attempts: IStepAttempt[];

  // accumulated metadata
  markers: IMarker[];
}

export interface ILogRetrievalShellCommand {
  stdout?: string | null;
  stderr?: string | null;
}

export interface ILogCaptureInfo {
  fileKey: string;
  stepKeys: string[];
  stepAttemptNumber?: number;
  pid?: string;
  externalStdoutUrl?: string;
  externalStderrUrl?: string;
  shellCmd?: ILogRetrievalShellCommand | null;
}

export interface IRunMetadataDict {
  firstLogAt: number;
  mostRecentLogAt: number;
  startingProcessAt?: number;
  startedProcessAt?: number;
  startedPipelineAt?: number;
  exitedAt?: number;
  processId?: number;
  globalMarkers: IMarker[];
  steps: {
    [stepKey: string]: IStepMetadata;
  };
  logCaptureSteps?: {
    [fileKey: string]: ILogCaptureInfo;
  };
}

export const EMPTY_RUN_METADATA: IRunMetadataDict = {
  firstLogAt: 0,
  mostRecentLogAt: 0,
  globalMarkers: [],
  steps: {},
};

export const extractLogCaptureStepsFromLegacySteps = (stepKeys: string[]) => {
  const logCaptureSteps: {[stepKey: string]: ILogCaptureInfo} = {};
  stepKeys.forEach((stepKey) => {
    logCaptureSteps[stepKey] = {fileKey: stepKey, stepKeys: [stepKey]};
  });
  return logCaptureSteps;
};

const fromTimestamp = (ts: number | null) => (ts ? Math.floor(ts * 1000) : undefined);

function extractMetadataFromRun(
  run: RunFragment | null = null,
  stepStats: RunStepStatsFragment['stepStats'] = [],
): IRunMetadataDict {
  const metadata: IRunMetadataDict = {
    firstLogAt: 0,
    mostRecentLogAt: 0,
    globalMarkers: [],
    steps: {},
  };

  if (!run) {
    return metadata;
  }
  if (run.startTime) {
    metadata.startedPipelineAt = fromTimestamp(run.startTime);
  }
  if (run.endTime) {
    metadata.exitedAt = fromTimestamp(run.endTime);
  }

  stepStats.forEach((stepStat) => {
    metadata.steps[stepStat.stepKey] = {
      // state:
      // current state
      state: stepStatusToStepState(stepStat.status),

      // execution start and stop (user-code) inclusive of all retries
      start: fromTimestamp(stepStat.startTime),
      end: fromTimestamp(stepStat.endTime),

      // current state + prev state transition times
      transitions: [],

      // transition times organized into start+stop+exit state pairs.
      // This is the metadata used to render boxes on the realtime vi.z
      attempts: stepStat.attempts.map(
        (attempt, idx) =>
          ({
            start: fromTimestamp(attempt.startTime),
            end: fromTimestamp(attempt.endTime),
            exitState:
              idx === stepStat.attempts.length - 1
                ? stepStatusToStepState(stepStat.status)
                : IStepState.RETRY_REQUESTED,
          }) as IStepAttempt,
      ),

      // accumulated metadata
      markers: stepStat.markers.map((marker, idx) => ({
        start: fromTimestamp(marker.startTime),
        end: fromTimestamp(marker.endTime),
        key: `marker_${idx}`,
      })),
    };
  });

  return metadata;
}

const stepStatusToStepState = (status: StepEventStatus | null) => {
  switch (status) {
    case StepEventStatus.SUCCESS:
      return IStepState.SUCCEEDED;
    case StepEventStatus.FAILURE:
      return IStepState.FAILED;
    case StepEventStatus.SKIPPED:
      return IStepState.SKIPPED;
    default:
      return IStepState.UNKNOWN;
  }
};

const refineMarkerEvent = (log: RunMetadataProviderMessageFragment) => {
  if (
    log.__typename === 'EngineEvent' ||
    log.__typename === 'ResourceInitFailureEvent' ||
    log.__typename === 'ResourceInitStartedEvent' ||
    log.__typename === 'ResourceInitSuccessEvent' ||
    log.__typename === 'StepWorkerStartedEvent' ||
    log.__typename === 'StepWorkerStartingEvent'
  ) {
    return log;
  }
  return null;
};

export function extractMetadataFromLogs(
  logs: RunMetadataProviderMessageFragment[],
): IRunMetadataDict {
  const metadata: IRunMetadataDict = {
    firstLogAt: 0,
    mostRecentLogAt: 0,
    globalMarkers: [],
    steps: {},
  };

  // Returns the most recent marker with the given `key` without an end time
  const upsertMarker = (set: IMarker[], key: string) => {
    let marker = set.find((f) => f.key === key && !f.end);
    if (!marker) {
      marker = {key};
      set.unshift(marker);
    }
    return marker;
  };

  const upsertState = (step: IStepMetadata, time: number, state: IStepState) => {
    step.transitions.push({time, state});
    step.state = state;
    step.attempts = [];
  };

  logs.forEach((log) => {
    const timestamp = Number.parseInt(log.timestamp, 10);

    metadata.firstLogAt = metadata.firstLogAt
      ? Math.min(metadata.firstLogAt, timestamp)
      : timestamp;
    metadata.mostRecentLogAt = Math.max(metadata.mostRecentLogAt, timestamp);

    if (log.__typename === 'RunStartEvent') {
      metadata.startedPipelineAt = timestamp;
    }
    if (
      log.__typename === 'RunFailureEvent' ||
      log.__typename === 'RunSuccessEvent' ||
      log.__typename === 'RunCanceledEvent'
    ) {
      metadata.exitedAt = timestamp;
      for (const step of Object.values(metadata.steps)) {
        if (step.state === IStepState.RUNNING) {
          upsertState(step, timestamp, IStepState.UNKNOWN);
        }
      }
    }

    if (!log.stepKey) {
      const markerEvent = refineMarkerEvent(log);
      if (markerEvent) {
        if (markerEvent.markerStart) {
          upsertMarker(metadata.globalMarkers, markerEvent.markerStart).start = timestamp;
        }
        if (markerEvent.markerEnd) {
          upsertMarker(metadata.globalMarkers, markerEvent.markerEnd).end = timestamp;
        }
      }
    }

    if (log.__typename === 'LogsCapturedEvent') {
      const singleStepKey = log.stepKeys?.length === 1 ? log.stepKeys[0] : null;
      const singleStepRetries =
        (singleStepKey &&
          metadata.steps[singleStepKey]?.transitions.filter(
            (s) => s.state === IStepState.RETRY_REQUESTED,
          ).length) ||
        null;

      if (!metadata.logCaptureSteps) {
        metadata.logCaptureSteps = {};
      }
      metadata.logCaptureSteps[log.fileKey] = {
        fileKey: log.fileKey,
        stepKeys: log.stepKeys || [],
        stepAttemptNumber: singleStepRetries ? singleStepRetries + 1 : undefined,
        pid: String(log.pid),
        externalStdoutUrl: log.externalStdoutUrl || undefined,
        externalStderrUrl: log.externalStderrUrl || undefined,
        shellCmd: log.shellCmd || undefined,
      };
    }

    if (log.stepKey) {
      const stepKey = log.stepKey;
      const step =
        metadata.steps[stepKey] ||
        ({
          state: undefined,
          attempts: [],
          transitions: [],
          start: undefined,
          end: undefined,
          markers: [],
        } as IStepMetadata);

      const markerEvent = refineMarkerEvent(log);
      if (markerEvent) {
        if (markerEvent.markerStart) {
          upsertMarker(step.markers, markerEvent.markerStart).start = timestamp;
        }
        if (markerEvent.markerEnd) {
          upsertMarker(step.markers, markerEvent.markerEnd).end = timestamp;
        }
      }

      if (log.__typename === 'StepWorkerStartingEvent') {
        upsertState(step, timestamp, IStepState.PREPARING);
      } else if (log.__typename === 'ExecutionStepStartEvent') {
        upsertState(step, timestamp, IStepState.RUNNING);
        step.start = timestamp;
      } else if (log.__typename === 'ExecutionStepSuccessEvent') {
        upsertState(step, timestamp, IStepState.SUCCEEDED);
        step.end = Math.max(timestamp, step.end || 0);
      } else if (log.__typename === 'ExecutionStepSkippedEvent') {
        upsertState(step, timestamp, IStepState.SKIPPED);
      } else if (log.__typename === 'ExecutionStepFailureEvent') {
        upsertState(step, timestamp, IStepState.FAILED);
        step.end = Math.max(timestamp, step.end || 0);
      } else if (log.__typename === 'ExecutionStepUpForRetryEvent') {
        // We only get one event when the step fails/aborts and is queued for retry,
        // but we create an "exit" state separate from the "preparing for retry" state
        // so that the box representing the attempt doesn't have a final state = preparing.
        // That'd be more confusing.
        upsertState(step, timestamp, IStepState.RETRY_REQUESTED);
        upsertState(step, timestamp + 1, IStepState.PREPARING);
      } else if (log.__typename === 'ExecutionStepRestartEvent') {
        upsertState(step, timestamp, IStepState.RUNNING);
      } else if (log.__typename === 'ObjectStoreOperationEvent') {
        // this indicates the step was skipped and its previous intermediates were copied
        // so we will drop the step because we didn't execute it
        if (log.operationResult.op === 'CP_OBJECT') {
          return;
        }
      }

      metadata.steps[stepKey] = step;
    }
  });

  // Post processing

  for (const step of Object.values(metadata.steps)) {
    // Sort step transitions because logs may not arrive in order
    step.transitions = step.transitions.sort((a, b) => a.time - b.time);

    // Build step "attempts" from transitions
    // - Each time we see a "RUNNING" step transition, we create a new attempt box unless one is open already.
    // - Each time we see a final step transition, we set it as the end state of the current attempt.

    let attempt: IStepAttempt | null = null;
    for (const t of step.transitions) {
      if ((!attempt || attempt.end) && t.state === IStepState.RUNNING) {
        attempt = {start: t.time};
        step.attempts.push(attempt);
      }
      if (attempt && BOX_EXIT_STATES.includes(t.state)) {
        attempt.end = t.time;
        attempt.exitState = t.state;
      }
    }

    // If a step is skipped, log an zero-second attempt so that the step is rendered
    // as a tiny dot on the chart.
    if (step.transitions.length === 1 && step.state === IStepState.SKIPPED) {
      step.attempts.push({
        start: step.transitions[0]!.time,
        end: step.transitions[0]!.time,
        exitState: IStepState.SKIPPED,
      });
    }
  }

  return metadata;
}

interface IRunMetadataProviderProps {
  logs: LogsProviderLogs;
  children: (metadata: IRunMetadataDict) => React.ReactElement<any>;
}

export const RunMetadataProvider = ({logs, children}: IRunMetadataProviderProps) => {
  const run = React.useContext(RunContext);

  // Step stats can be expensive to load, so we separate them from the main run query.
  const {data} = useQuery<RunStepStatsQuery, RunStepStatsQueryVariables>(RUN_STEP_STATS_QUERY, {
    variables: run ? {runId: run.id} : undefined,
    skip: !run,
  });

  const stepStats = useMemo(() => {
    return data?.pipelineRunOrError.__typename === 'Run' ? data.pipelineRunOrError.stepStats : [];
  }, [data]);

  const runMetadata = React.useMemo(() => extractMetadataFromRun(run, stepStats), [run, stepStats]);
  const metadata = React.useMemo(
    () =>
      logs.loading ? runMetadata : extractMetadataFromLogs(flattenOneLevel(logs.allNodeChunks)),
    [logs, runMetadata],
  );
  return <>{children(metadata)}</>;
};

const RUN_STEP_STATS_QUERY = gql`
  query RunStepStatsQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        ...RunStepStatsFragment
      }
    }
  }

  fragment RunStepStatsFragment on Run {
    id
    stepStats {
      stepKey
      status
      startTime
      endTime
      attempts {
        startTime
        endTime
      }
      markers {
        startTime
        endTime
      }
    }
  }
`;

export const RUN_METADATA_PROVIDER_MESSAGE_FRAGMENT = gql`
  fragment RunMetadataProviderMessageFragment on DagsterRunEvent {
    ... on MessageEvent {
      message
      timestamp
      stepKey
    }
    ... on MarkerEvent {
      markerStart
      markerEnd
    }
    ... on ObjectStoreOperationEvent {
      operationResult {
        op
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
    }
    ... on LogsCapturedEvent {
      fileKey
      stepKeys
      pid
      externalStdoutUrl
      externalStderrUrl
      shellCmd {
        stdout
        stderr
      }
    }
  }

  ${METADATA_ENTRY_FRAGMENT}
`;
