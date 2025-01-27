import {
  Box,
  Button,
  Colors,
  Dialog,
  DialogFooter,
  Icon,
  Mono,
  Spinner,
} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {CapturedOrExternalLogPanel} from './CapturedLogPanel';
import {DefaultLogLevels} from './LogLevel';
import {LogFilter, LogsProvider, LogsProviderLogs} from './LogsProvider';
import {LogsScrollingTable} from './LogsScrollingTable';
import {LogType, LogsToolbar} from './LogsToolbar';
import {IRunMetadataDict, RunMetadataProvider} from './RunMetadataProvider';
import {titleForRun} from './RunUtils';
import {useComputeLogFileKeyForSelection} from './useComputeLogFileKeyForSelection';
import {DagsterEventType} from '../graphql/types';
import {flattenOneLevel} from '../util/flattenOneLevel';

export function useStepLogs({runId, stepKeys}: {runId?: string; stepKeys?: string[]}) {
  const [showingLogs, setShowingLogs] = React.useState<{runId: string; stepKeys: string[]} | null>(
    null,
  );

  // Note: This hook captures the runId + stepKeys in state when you click the button and then passes
  // those values to the modal. This ensures that the modal is "stable" while it's open, even if
  // the runId passed to the hook changes or becomes undefined. (eg: "Currently materializing" banner)

  return {
    dialog: (
      <StepLogsDialog
        runId={showingLogs?.runId}
        stepKeys={showingLogs?.stepKeys || []}
        onClose={() => setShowingLogs(null)}
      />
    ),
    button:
      runId && stepKeys ? (
        <Button
          small
          icon={<Icon name="wysiwyg" />}
          onClick={() => setShowingLogs({runId, stepKeys})}
        >
          View logs
        </Button>
      ) : undefined,
  };
}

export const StepLogsDialog = ({
  runId,
  stepKeys,
  onClose,
}: {
  runId?: string;
  stepKeys: string[];
  onClose: () => void;
}) => {
  return (
    <Dialog
      isOpen={!!runId}
      style={{width: '80vw'}}
      canOutsideClickClose
      canEscapeKeyClose
      onClose={onClose}
    >
      {runId ? (
        <LogsProvider key={runId} runId={runId}>
          {(logs) => (
            <RunMetadataProvider logs={logs}>
              {(metadata) => (
                <StepLogsDialogContent
                  runId={runId}
                  metadata={metadata}
                  stepKeys={stepKeys}
                  logs={logs}
                />
              )}
            </RunMetadataProvider>
          )}
        </LogsProvider>
      ) : (
        ''
      )}
      <div style={{zIndex: 2, background: Colors.backgroundDefault()}}>
        <DialogFooter topBorder>
          <Button intent="primary" onClick={onClose}>
            Done
          </Button>
        </DialogFooter>
      </div>
    </Dialog>
  );
};

export const StepLogsDialogContent = ({
  runId,
  stepKeys,
  metadata,
  logs,
}: {
  runId: string;
  stepKeys: string[];
  metadata: IRunMetadataDict;
  logs: LogsProviderLogs;
}) => {
  const [logType, setComputeLogType] = useState<LogType>(LogType.structured);
  const [computeLogUrl, setComputeLogUrl] = React.useState<string | null>(null);

  const flatLogs = useMemo(() => flattenOneLevel(logs.allNodeChunks), [logs]);

  const stepKeysSet = useMemo(() => new Set(stepKeys), [stepKeys]);

  const firstLogForStep = flatLogs.find(
    (l) => l.eventType === DagsterEventType.STEP_START && l.stepKey && stepKeysSet.has(l.stepKey),
  );

  const firstLogForStepTime = firstLogForStep ? Number(firstLogForStep.timestamp) : 0;

  const [filter, setFilter] = useState<LogFilter>({
    hideNonMatches: false,
    focusedTime: firstLogForStepTime,
    levels: Object.fromEntries(DefaultLogLevels.map((l) => [l, true])),
    logQuery: stepKeys.map((stepKey) => ({token: 'step', value: stepKey})),
    sinceTime: 0,
  });

  React.useEffect(() => {
    setFilter((filter) => ({...filter, focusedTime: firstLogForStepTime}));
  }, [firstLogForStepTime]);

  const {computeLogFileKey, setComputeLogFileKey, logCaptureInfo} =
    useComputeLogFileKeyForSelection({
      metadata,
      stepKeys,
      selectionStepKeys: stepKeys,
    });

  return (
    <LogsContainer>
      <LogsToolbar
        metadata={metadata}
        logType={logType}
        onSetLogType={setComputeLogType}
        computeLogFileKey={computeLogFileKey}
        onSetComputeLogKey={setComputeLogFileKey}
        computeLogUrl={computeLogUrl}
        steps={[]}
        counts={logs.counts}
        filter={filter}
        onSetFilter={setFilter}
      >
        <Link to={`/runs/${runId}?stepKeys=${stepKeys}`} style={{marginLeft: 8}}>
          <Box flex={{gap: 4, alignItems: 'center'}}>
            {!metadata.exitedAt && logType === LogType.structured && (
              <Spinner purpose="body-text" />
            )}
            View Run <Mono>{titleForRun({id: runId})}</Mono>
            <Icon name="open_in_new" color={Colors.linkDefault()} />
          </Box>
        </Link>
      </LogsToolbar>

      {logType !== LogType.structured ? (
        <CapturedOrExternalLogPanel
          logKey={computeLogFileKey ? [runId, 'compute_logs', computeLogFileKey] : []}
          logCaptureInfo={logCaptureInfo}
          visibleIOType={LogType[logType]}
          onSetDownloadUrl={setComputeLogUrl}
        />
      ) : (
        <LogsScrollingTable
          logs={logs}
          filter={filter}
          filterStepKeys={stepKeys}
          filterKey={`${JSON.stringify(filter)}`}
          metadata={metadata}
        />
      )}
    </LogsContainer>
  );
};

const LogsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 65vh;
`;
