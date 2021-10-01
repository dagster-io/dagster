import {gql} from '@apollo/client';
import * as React from 'react';
import {METADATA_ENTRY_FRAGMENT} from './MetadataEntry';

import {RunMetadataProviderMessageFragment} from './types/RunMetadataProviderMessageFragment';

export enum IStepState {
  PREPARING = 'preparing',
  RETRY_REQUESTED = 'retry-requested',
  RUNNING = 'running',
  SUCCEEDED = 'succeeded',
  SKIPPED = 'skipped',
  FAILED = 'failed',
  UNKNOWN = 'unknown',
}

const BOX_EXIT_STATES = [IStepState.RETRY_REQUESTED, IStepState.SUCCEEDED, IStepState.FAILED];

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
  state: IStepState;

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

export interface ILogCaptureInfo {
  logKey: string;
  stepKeys: string[];
  pid?: string;
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
    [logKey: string]: ILogCaptureInfo;
  };
}

export const EMPTY_RUN_METADATA: IRunMetadataDict = {
  firstLogAt: 0,
  mostRecentLogAt: 0,
  globalMarkers: [],
  steps: {},
};

export const extractLogCaptureStepsFromLegacySteps = (stepKeys: string[]) => {
  const logCaptureSteps = {};
  stepKeys.forEach(
    (stepKey) => (logCaptureSteps[stepKey] = {logKey: stepKey, stepKeys: [stepKey]}),
  );
  return logCaptureSteps;
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

    if (log.__typename === 'PipelineStartEvent') {
      metadata.startedPipelineAt = timestamp;
    }
    if (
      log.__typename === 'PipelineFailureEvent' ||
      log.__typename === 'PipelineSuccessEvent' ||
      log.__typename === 'PipelineCanceledEvent'
    ) {
      metadata.exitedAt = timestamp;
      for (const step of Object.values(metadata.steps)) {
        if (step.state === IStepState.RUNNING) {
          upsertState(step, timestamp, IStepState.UNKNOWN);
        }
      }
    }

    if (log.__typename === 'EngineEvent' && !log.stepKey) {
      if (log.markerStart) {
        upsertMarker(metadata.globalMarkers, log.markerStart).start = timestamp;
      }
      if (log.markerEnd) {
        upsertMarker(metadata.globalMarkers, log.markerEnd).end = timestamp;
      }
    }

    if (log.__typename === 'LogsCapturedEvent') {
      if (!metadata.logCaptureSteps) {
        metadata.logCaptureSteps = {};
      }
      metadata.logCaptureSteps[log.logKey] = {
        logKey: log.logKey,
        stepKeys: log.stepKeys || [],
        pid: String(log.pid),
      };
    }

    if (log.stepKey) {
      const stepKey = log.stepKey;
      const step =
        metadata.steps[stepKey] ||
        ({
          state: IStepState.PREPARING,
          attempts: [],
          transitions: [
            {
              state: IStepState.PREPARING,
              time: timestamp,
            },
          ],
          start: undefined,
          end: undefined,
          markers: [],
        } as IStepMetadata);

      if (log.__typename === 'ExecutionStepStartEvent') {
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
      } else if (log.__typename === 'EngineEvent') {
        if (log.markerStart) {
          upsertMarker(step.markers, log.markerStart).start = timestamp;
        }
        if (log.markerEnd) {
          upsertMarker(step.markers, log.markerEnd).end = timestamp;
        }
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
    let start = null;
    for (const t of step.transitions) {
      if (t.state === IStepState.RUNNING) {
        start = t.time;
      }
      if (start && BOX_EXIT_STATES.includes(t.state)) {
        step.attempts.push({start, end: t.time, exitState: t.state});
        start = null;
      }
    }
    if (start !== null) {
      step.attempts.push({start});
    }
  }

  return metadata;
}

interface IRunMetadataProviderProps {
  logs: RunMetadataProviderMessageFragment[];
  children: (metadata: IRunMetadataDict) => React.ReactElement<any>;
}

export const RunMetadataProvider: React.FC<IRunMetadataProviderProps> = ({logs, children}) => {
  const metadata = React.useMemo(() => extractMetadataFromLogs(logs), [logs]);
  return <>{children(metadata)}</>;
};

export const RUN_METADATA_PROVIDER_MESSAGE_FRAGMENT = gql`
  fragment RunMetadataProviderMessageFragment on PipelineRunEvent {
    __typename
    ... on MessageEvent {
      message
      timestamp
      stepKey
    }
    ... on EngineEvent {
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
      logKey
      stepKeys
      pid
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
`;
