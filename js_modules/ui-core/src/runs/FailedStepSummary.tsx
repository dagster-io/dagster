import {Box, Button, Colors, Icon, Text} from '@dagster-io/ui-components';
import * as React from 'react';

import {LogsProviderLogs} from './LogsProvider';
import {IRunMetadataDict, IStepState} from './RunMetadataProvider';
import styles from './css/FailedStepSummary.module.css';
import {LogNode} from './types';
import {RunDagsterRunEventFragment} from './types/RunFragments.types';

interface Props {
  logs: LogsProviderLogs;
  metadata: IRunMetadataDict;
  onSelectStep: (stepKey: string) => void;
  onShowDetails: (stepKey: string, logs: RunDagsterRunEventFragment[]) => void;
}

/**
 * Failure-first summary for the phone run page: which step failed and what it
 * said, without scrolling through the log table. Rendered above the logs when
 * the run has failed.
 */
export const FailedStepSummary = ({logs, metadata, onSelectStep, onShowDetails}: Props) => {
  const summary = React.useMemo(() => summarizeFailure(logs, metadata), [logs, metadata]);

  if (!summary) {
    return null;
  }

  const {stepKey, message, otherFailedCount, allNodes} = summary;

  return (
    <Box
      className={styles.container}
      padding={{vertical: 8, horizontal: 12}}
      border="bottom"
      flex={{direction: 'column', gap: 4}}
    >
      <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
        <Icon name="error" color={Colors.accentRed()} size={16} />
        <Text size={12} color="textLight">
          {stepKey ? 'Failed step' : 'Run failed'}
        </Text>
      </Box>
      {stepKey ? (
        <Text size={14} family="mono" className={styles.stepKey}>
          {stepKey}
        </Text>
      ) : null}
      {message ? <div className={styles.message}>{message}</div> : null}
      {otherFailedCount > 0 ? (
        <Text size={12} color="textLight">
          {otherFailedCount} more failed {otherFailedCount === 1 ? 'step' : 'steps'}
        </Text>
      ) : null}
      {stepKey ? (
        <Box flex={{direction: 'row', gap: 8, wrap: 'wrap'}} margin={{top: 4}}>
          <Button icon={<Icon name="filter_alt" />} onClick={() => onSelectStep(stepKey)}>
            Show step logs
          </Button>
          <Button
            icon={<Icon name="open_in_new" />}
            onClick={() => onShowDetails(stepKey, allNodes)}
          >
            Full error
          </Button>
        </Box>
      ) : null}
    </Box>
  );
};

interface FailureSummary {
  stepKey: string | null;
  message: string | null;
  otherFailedCount: number;
  allNodes: LogNode[];
}

const MAX_MESSAGE_CHARS = 280;

const firstLines = (text: string) => {
  const trimmed = text.trim();
  return trimmed.length > MAX_MESSAGE_CHARS ? `${trimmed.slice(0, MAX_MESSAGE_CHARS)}…` : trimmed;
};

export const summarizeFailure = (
  logs: LogsProviderLogs,
  metadata: IRunMetadataDict,
): FailureSummary | null => {
  const allNodes = logs.allNodeChunks.flat();

  const failedSteps = Object.keys(metadata.steps).filter(
    (key) => metadata.steps[key]?.state === IStepState.FAILED,
  );

  if (failedSteps.length) {
    // The first step to fail is usually the root cause; later failures are
    // often downstream steps that never ran.
    const sorted = [...failedSteps].sort(
      (a, b) => (metadata.steps[a]?.end ?? 0) - (metadata.steps[b]?.end ?? 0),
    );
    const stepKey = sorted[0] as string;
    const failureEvent = allNodes.find(
      (node) => node.__typename === 'ExecutionStepFailureEvent' && node.stepKey === stepKey,
    );
    const message =
      failureEvent && failureEvent.__typename === 'ExecutionStepFailureEvent'
        ? (failureEvent.error?.message ?? failureEvent.message)
        : null;
    return {
      stepKey,
      message: message ? firstLines(message) : null,
      otherFailedCount: failedSteps.length - 1,
      allNodes,
    };
  }

  const runFailure = allNodes.find((node) => node.__typename === 'RunFailureEvent');
  if (runFailure && runFailure.__typename === 'RunFailureEvent') {
    const message = runFailure.error?.message ?? runFailure.message;
    return {
      stepKey: null,
      message: message ? firstLines(message) : null,
      otherFailedCount: 0,
      allNodes,
    };
  }

  return null;
};
