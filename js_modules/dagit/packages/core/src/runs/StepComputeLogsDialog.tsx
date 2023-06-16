import {Box, Button, Colors, Dialog, DialogFooter, Icon, Mono} from '@dagster-io/ui';
import React, {useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useSupportsCapturedLogs} from '../instance/useSupportsCapturedLogs';

import {CapturedOrExternalLogPanel} from './CapturedLogPanel';
import {ComputeLogPanel} from './ComputeLogPanel';
import {DefaultLogLevels} from './LogLevel';
import {LogFilter, LogsProvider, LogsProviderLogs} from './LogsProvider';
import {LogsScrollingTable} from './LogsScrollingTable';
import {LogType, LogsToolbar} from './LogsToolbar';
import {IRunMetadataDict, RunMetadataProvider} from './RunMetadataProvider';
import {titleForRun} from './RunUtils';
import {useComputeLogFileKeyForSelection} from './useComputeLogFileKeyForSelection';

export const StepComputeLogsDialog: React.FC<{
  runId: string;
  stepKeys: string[];
  isOpen: boolean;
  onClose: () => void;
}> = ({runId, stepKeys, isOpen, onClose}) => {
  return (
    <Dialog
      isOpen={isOpen}
      style={{width: '80vw'}}
      canOutsideClickClose
      canEscapeKeyClose
      onClose={onClose}
    >
      {isOpen ? (
        <LogsProvider key={runId} runId={runId}>
          {(logs) => (
            <RunMetadataProvider logs={logs}>
              {(metadata) => (
                <StepComputeLogsModalContent
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
      <div style={{zIndex: 2, background: Colors.White}}>
        <DialogFooter topBorder>
          <Button intent="primary" onClick={onClose}>
            Done
          </Button>
        </DialogFooter>
      </div>
    </Dialog>
  );
};

export const StepComputeLogsModalContent: React.FC<{
  runId: string;
  stepKeys: string[];
  metadata: IRunMetadataDict;
  logs: LogsProviderLogs;
}> = ({runId, stepKeys, metadata, logs}) => {
  const supportsCapturedLogs = useSupportsCapturedLogs();
  const [logType, setComputeLogType] = useState<LogType>(LogType.structured);
  const [computeLogUrl, setComputeLogUrl] = React.useState<string | null>(null);
  const [filter, setFilter] = useState<LogFilter>({
    hideNonMatches: true,
    focusedTime: 0,
    levels: Object.fromEntries(DefaultLogLevels.map((l) => [l, true])),
    logQuery: [],
    sinceTime: 0,
  });

  const {
    computeLogFileKey,
    setComputeLogFileKey,
    logCaptureInfo,
  } = useComputeLogFileKeyForSelection({
    metadata,
    stepKeys,
    selectionStepKeys: stepKeys,
  });

  // The user can add MORE filters in the filter input, but we truncate the logs
  // to just the ones for the modal's step keys so it's not possible to un-hide them by
  // clearing the filter input. This also makes them appear white by default, rather than
  // being highlighted as "filter matches".
  const logsFilteredToSteps = React.useMemo(() => {
    return {
      ...logs,
      allNodes: logs.allNodes.filter((node) => node.stepKey && stepKeys.includes(node.stepKey)),
    };
  }, [logs, stepKeys]);

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
        <Link to={`/runs/${runId}?stepKeys=${stepKeys}`}>
          <Box flex={{gap: 4, alignItems: 'center'}}>
            View Run <Mono>{titleForRun({id: runId})}</Mono>
            <Icon name="open_in_new" color={Colors.Link} />
          </Box>
        </Link>
      </LogsToolbar>

      {logType !== LogType.structured ? (
        supportsCapturedLogs ? (
          <CapturedOrExternalLogPanel
            logKey={computeLogFileKey ? [runId, 'compute_logs', computeLogFileKey] : []}
            logCaptureInfo={logCaptureInfo}
            visibleIOType={LogType[logType]}
            onSetDownloadUrl={setComputeLogUrl}
          />
        ) : (
          <ComputeLogPanel
            runId={runId}
            computeLogFileKey={computeLogFileKey}
            ioType={LogType[logType]}
            setComputeLogUrl={setComputeLogUrl}
          />
        )
      ) : (
        <LogsScrollingTable
          logs={logsFilteredToSteps}
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
