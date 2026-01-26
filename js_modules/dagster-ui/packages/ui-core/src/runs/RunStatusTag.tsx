import {
  Box,
  Button,
  CaptionMono,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Popover,
  Subtitle2,
  Tag,
} from '@dagster-io/ui-components';
import {useState} from 'react';

import {IRunFailureEvent} from './RunMetadataProvider';
import {RunStats} from './RunStats';
import {RunStatusIndicator} from './RunStatusDots';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {assertUnreachable} from '../app/Util';
import {RunStatus} from '../graphql/types';

const statusToIntent = (status: RunStatus) => {
  switch (status) {
    case RunStatus.QUEUED:
    case RunStatus.NOT_STARTED:
    case RunStatus.CANCELED:
    case RunStatus.MANAGED:
      return 'none';
    case RunStatus.SUCCESS:
      return 'success';
    case RunStatus.FAILURE:
      return 'danger';
    case RunStatus.STARTING:
    case RunStatus.STARTED:
    case RunStatus.CANCELING:
      return 'primary';
    default:
      return assertUnreachable(status);
  }
};

const runStatusToString = (status: RunStatus) => {
  switch (status) {
    case RunStatus.QUEUED:
      return 'Queued';
    case RunStatus.SUCCESS:
      return 'Success';
    case RunStatus.STARTING:
      return 'Starting';
    case RunStatus.NOT_STARTED:
      return 'Not started';
    case RunStatus.FAILURE:
      return 'Failure';
    case RunStatus.STARTED:
      return 'Started';
    case RunStatus.MANAGED:
      return 'Managed';
    case RunStatus.CANCELING:
      return 'Canceling';
    case RunStatus.CANCELED:
      return 'Canceled';
    default:
      return assertUnreachable(status);
  }
};

export const runStatusToBackfillStateString = (status: RunStatus) => {
  switch (status) {
    case RunStatus.CANCELED:
      return 'Canceled';
    case RunStatus.CANCELING:
      return 'Canceling';
    case RunStatus.FAILURE:
      return 'Failed';
    case RunStatus.STARTING:
    case RunStatus.STARTED:
      return 'In progress';
    case RunStatus.QUEUED:
      return 'Queued';
    case RunStatus.SUCCESS:
      return 'Completed';
    case RunStatus.MANAGED:
    case RunStatus.NOT_STARTED:
      return 'Missing';
    default:
      return assertUnreachable(status);
  }
};

export const RUN_STATUS_COLORS = {
  QUEUED: Colors.accentGray(),
  NOT_STARTED: Colors.accentGrayHover(),
  MANAGED: Colors.accentGray(),
  STARTED: Colors.accentBlue(),
  STARTING: Colors.accentBlue(),
  CANCELING: Colors.accentBlue(),
  SUCCESS: Colors.accentGreen(),
  FAILURE: Colors.accentRed(),
  CANCELED: Colors.accentRed(),

  // Not technically a RunStatus, but useful.
  SCHEDULED: Colors.accentGray(),
};

export const RunStatusTag = (props: {status: RunStatus; failureInfo?: IRunFailureEvent | null}) => {
  const {status, failureInfo} = props;
  const [showDialog, setShowDialog] = useState(false);

  const isClickable = status === RunStatus.FAILURE && !!failureInfo;

  const tag = (
    <Tag intent={statusToIntent(status)} interactive={isClickable}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        <RunStatusIndicator status={status} size={10} />
        <div>{runStatusToString(status)}</div>
      </Box>
    </Tag>
  );

  return (
    <>
      {isClickable ? (
        <span onClick={() => setShowDialog(true)} style={{cursor: 'pointer'}}>
          {tag}
        </span>
      ) : (
        tag
      )}
      {failureInfo && (
        <Dialog
          title="Run Failure"
          isOpen={showDialog}
          canEscapeKeyClose
          canOutsideClickClose
          onClose={() => setShowDialog(false)}
          style={{width: 'auto', maxWidth: '80vw'}}
        >
          <RunFailureDialogContents
            failureInfo={failureInfo}
            onClose={() => setShowDialog(false)}
          />
        </Dialog>
      )}
    </>
  );
};

export const RunStatusTagWithID = ({runId, status}: {runId: string; status: RunStatus}) => {
  return (
    <Tag intent={statusToIntent(status)}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        <RunStatusIndicator status={status} size={10} />
        <CaptionMono>{runId.slice(0, 8)}</CaptionMono>
      </Box>
    </Tag>
  );
};

interface Props {
  runId: string;
  status: RunStatus;
}

export const RunStatusTagWithStats = (props: Props) => {
  const {runId, status} = props;
  return (
    <Popover
      position="bottom-left"
      interactionKind="hover"
      content={<RunStats runId={runId} />}
      hoverOpenDelay={100}
      usePortal
    >
      <RunStatusTag status={status} />
    </Popover>
  );
};

// Helper to check if an error has a stack trace
const hasStackTrace = (error: {
  message: string;
  stack?: string[];
  errorChain?: {error: {stack?: string[]}}[];
}) => {
  if (error.stack && error.stack.length > 0) {
    return true;
  }
  if (error.errorChain) {
    return error.errorChain.some((chain) => chain.error.stack && chain.error.stack.length > 0);
  }
  return false;
};

const RunFailureDialogContents = ({
  failureInfo,
  onClose,
}: {
  failureInfo: IRunFailureEvent;
  onClose: () => void;
}) => {
  const runFailureError = failureInfo.error ?? {message: failureInfo.message};
  const showRunFailureBox = hasStackTrace(runFailureError);

  const firstStepError =
    failureInfo.firstStepFailure?.error ??
    (failureInfo.firstStepFailure ? {message: failureInfo.firstStepFailure.message} : null);

  // CSS to override inner scrolling - make the whole dialog scroll instead
  // Target the ErrorWrapper div (CSS modules generate class names containing "wrapper")
  const noInnerScrollStyle = `
    .run-failure-dialog-content [class*="wrapper"] {
      max-height: none !important;
      overflow: visible !important;
    }
  `;

  return (
    <>
      <style>{noInnerScrollStyle}</style>
      <DialogBody>
        <div
          className="run-failure-dialog-content"
          style={{maxHeight: 'calc(100vh - 200px)', overflow: 'auto'}}
        >
          {/* Run Failure first */}
          <Box margin={{bottom: failureInfo.firstStepFailure ? 16 : 0}}>
            <Subtitle2>Run Failure</Subtitle2>
            {showRunFailureBox ? (
              <Box margin={{top: 8}}>
                <PythonErrorInfo error={runFailureError} />
              </Box>
            ) : (
              <div style={{marginTop: 8}}>{runFailureError.message}</div>
            )}
          </Box>

          {/* First Step Failure second */}
          {failureInfo.firstStepFailure && firstStepError && (
            <Box>
              <Subtitle2>First Step Failure: {failureInfo.firstStepFailure.stepKey}</Subtitle2>
              <Box margin={{top: 8}}>
                <PythonErrorInfo
                  error={firstStepError}
                  errorSource={failureInfo.firstStepFailure.errorSource}
                />
              </Box>
            </Box>
          )}
        </div>
      </DialogBody>
      <DialogFooter topBorder>
        <Button intent="primary" onClick={onClose}>
          Close
        </Button>
      </DialogFooter>
    </>
  );
};
