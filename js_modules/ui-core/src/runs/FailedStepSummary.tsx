import {Box, Button, Colors, Icon, Text} from '@dagster-io/ui-components';
import * as React from 'react';

import {LogsProviderLogs} from './LogsProvider';
import {IRunMetadataDict, IStepState} from './RunMetadataProvider';
import styles from './css/FailedStepSummary.module.css';
import {LogNode} from './types';

/** The events that mark a step as failed in RunMetadataProvider. */
export type StepFailureNode = Extract<
  LogNode,
  {__typename: 'ExecutionStepFailureEvent' | 'ResourceInitFailureEvent'}
>;

interface Props {
  logs: LogsProviderLogs;
  metadata: IRunMetadataDict;
  onSelectStep: (stepKey: string) => void;
  onShowDetails: (failureNode: StepFailureNode) => void;
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

  const {stepKey, message, otherFailedCount, failureNode} = summary;

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
      {message ? (
        <div className={styles.message}>{message}</div>
      ) : stepKey ? (
        <Text size={12} color="textLight">
          Error details aren&apos;t in the loaded logs. Show step logs to see the full output.
        </Text>
      ) : null}
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
          {failureNode ? (
            <Button icon={<Icon name="open_in_new" />} onClick={() => onShowDetails(failureNode)}>
              Full error
            </Button>
          ) : null}
        </Box>
      ) : null}
    </Box>
  );
};

interface FailureSummary {
  stepKey: string | null;
  message: string | null;
  otherFailedCount: number;
  failureNode: StepFailureNode | null;
}

const MAX_MESSAGE_CHARS = 280;

const firstLines = (text: string) => {
  const trimmed = text.trim();
  return trimmed.length > MAX_MESSAGE_CHARS ? `${trimmed.slice(0, MAX_MESSAGE_CHARS)}…` : trimmed;
};

const isStepFailureNode = (node: LogNode): node is StepFailureNode =>
  node.__typename === 'ExecutionStepFailureEvent' || node.__typename === 'ResourceInitFailureEvent';

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
    // A step is FAILED after either event; the failure event may also be
    // missing entirely when the logs are capped or still loading.
    const failureNode =
      allNodes.find(
        (node): node is StepFailureNode => isStepFailureNode(node) && node.stepKey === stepKey,
      ) ?? null;
    const message = failureNode ? (failureNode.error?.message ?? failureNode.message) : null;
    return {
      stepKey,
      message: message ? firstLines(message) : null,
      otherFailedCount: failedSteps.length - 1,
      failureNode,
    };
  }

  const runFailure = allNodes.find((node) => node.__typename === 'RunFailureEvent');
  if (runFailure && runFailure.__typename === 'RunFailureEvent') {
    const message = runFailure.error?.message ?? runFailure.message;
    return {
      stepKey: null,
      message: message ? firstLines(message) : null,
      otherFailedCount: 0,
      failureNode: null,
    };
  }

  return null;
};
