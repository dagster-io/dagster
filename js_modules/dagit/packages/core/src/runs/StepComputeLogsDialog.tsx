import {Box, Button, Colors, Dialog, DialogBody, DialogFooter, Icon, Mono} from '@dagster-io/ui';
import React, {useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useSupportsCapturedLogs} from '../instance/useSupportsCapturedLogs';

import {CapturedOrExternalLogPanel} from './CapturedLogPanel';
import {ComputeLogPanel} from './ComputeLogPanel';
import {LogsProvider} from './LogsProvider';
import {ComputeLogToolbar, LogType} from './LogsToolbar';
import {
  ILogCaptureInfo,
  IRunMetadataDict,
  RunMetadataProvider,
  matchingComputeLogKeyFromStepKey,
} from './RunMetadataProvider';
import {titleForRun} from './RunUtils';

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
      <DialogBody>
        {isOpen ? (
          <LogsProvider key={runId} runId={runId}>
            {(logs) => (
              <RunMetadataProvider logs={logs}>
                {(metadata) => (
                  <StepComputeLogsModalContent
                    runId={runId}
                    metadata={metadata}
                    stepKeys={stepKeys}
                  />
                )}
              </RunMetadataProvider>
            )}
          </LogsProvider>
        ) : (
          ''
        )}
      </DialogBody>
      <DialogFooter topBorder>
        <Button intent="primary" onClick={onClose}>
          Done
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

export const StepComputeLogsModalContent: React.FC<{
  runId: string;
  stepKeys: string[];
  metadata: IRunMetadataDict;
}> = ({runId, stepKeys, metadata}) => {
  const supportsCapturedLogs = useSupportsCapturedLogs();
  const [logType, setComputeLogType] = useState<LogType>(LogType.stdout);
  const [computeLogUrl, setComputeLogUrl] = React.useState<string | null>(null);
  const [computeLogFileKey, setComputeLogFileKey] = React.useState<string>('');

  const logCaptureInfo: ILogCaptureInfo | undefined =
    metadata.logCaptureSteps && computeLogFileKey in metadata.logCaptureSteps
      ? metadata.logCaptureSteps[computeLogFileKey]
      : undefined;

  React.useEffect(() => {
    if (!stepKeys?.length || computeLogFileKey) {
      return;
    }

    if (metadata.logCaptureSteps) {
      const logFileKeys = Object.keys(metadata.logCaptureSteps);
      const selectedLogKey = logFileKeys.find((logFileKey) => {
        return stepKeys.every(
          (stepKey) =>
            metadata.logCaptureSteps &&
            metadata.logCaptureSteps[logFileKey].stepKeys.includes(stepKey),
        );
      });
      setComputeLogFileKey(selectedLogKey || logFileKeys[0]);
    } else if (!stepKeys.includes(computeLogFileKey)) {
      const matching = matchingComputeLogKeyFromStepKey(metadata.logCaptureSteps, stepKeys[0]);
      matching && setComputeLogFileKey(matching);
    } else if (stepKeys.length === 1 && computeLogFileKey !== stepKeys[0]) {
      const matching = matchingComputeLogKeyFromStepKey(metadata.logCaptureSteps, stepKeys[0]);
      matching && setComputeLogFileKey(matching);
    }
  }, [stepKeys, computeLogFileKey, metadata.logCaptureSteps, setComputeLogFileKey]);

  return (
    <LogsContainer>
      <Box flex={{direction: 'row', alignItems: 'baseline', gap: 16}}>
        <ComputeLogToolbar
          metadata={metadata}
          logType={logType}
          onSetLogType={setComputeLogType}
          computeLogFileKey={computeLogFileKey}
          onSetComputeLogKey={setComputeLogFileKey}
          computeLogUrl={computeLogUrl}
        />
        <Link to={`/runs/${runId}?stepKeys=${stepKeys}`}>
          <Box flex={{gap: 4, alignItems: 'center'}}>
            View Run <Mono>{titleForRun({id: runId})}</Mono>
            <Icon name="open_in_new" color={Colors.Link} />
          </Box>
        </Link>
      </Box>
      {supportsCapturedLogs ? (
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
