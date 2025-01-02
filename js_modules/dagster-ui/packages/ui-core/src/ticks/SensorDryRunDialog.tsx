import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Group,
  Icon,
  NonIdealState,
  NonIdealStateWrapper,
  Spinner,
  Subheading,
  Tag,
  TextInput,
  Tooltip,
} from '@dagster-io/ui-components';
import {useCallback, useMemo, useState} from 'react';
import styled from 'styled-components';

import {RunRequestTable} from './DryRunRequestTable';
import {DynamicPartitionRequests} from './DynamicPartitionRequests';
import {RUN_REQUEST_FRAGMENT} from './RunRequestFragment';
import {gql, useMutation} from '../apollo-client';
import {
  SensorDryRunMutation,
  SensorDryRunMutationVariables,
} from './types/SensorDryRunDialog.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {showSharedToaster} from '../app/DomUtils';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {assertUnreachable} from '../app/Util';
import {useTrackEvent} from '../app/analytics';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {SensorSelector} from '../graphql/types';
import {useLaunchMultipleRunsWithTelemetry} from '../launchpad/useLaunchMultipleRunsWithTelemetry';
import {SET_CURSOR_MUTATION} from '../sensors/EditCursorDialog';
import {
  SetSensorCursorMutation,
  SetSensorCursorMutationVariables,
} from '../sensors/types/EditCursorDialog.types';
import {testId} from '../testing/testId';
import {buildExecutionParamsListSensor} from '../util/buildExecutionParamsList';
import {RepoAddress} from '../workspace/types';

export type SensorDryRunInstigationTick = Extract<
  SensorDryRunMutation['sensorDryRun'],
  {__typename: 'DryRunInstigationTick'}
>;

type Props = {
  name: string;
  onClose: () => void;
  repoAddress: RepoAddress;
  currentCursor: string;
  isOpen: boolean;
  jobName: string;
};

export const SensorDryRunDialog = (props: Props) => {
  const {isOpen, onClose, name} = props;
  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      style={{width: '70vw', display: 'flex'}}
      icon="preview_tick"
      title={`Preview tick result for ${name}`}
    >
      <SensorDryRun {...props} />
    </Dialog>
  );
};

const SensorDryRun = ({repoAddress, name, currentCursor, onClose, jobName}: Props) => {
  const trackEvent = useTrackEvent();

  const [sensorDryRun] = useMutation<SensorDryRunMutation, SensorDryRunMutationVariables>(
    EVALUATE_SENSOR_MUTATION,
  );
  const [setCursorMutation] = useMutation<
    SetSensorCursorMutation,
    SetSensorCursorMutationVariables
  >(SET_CURSOR_MUTATION);

  const [cursor, setCursor] = useState(currentCursor);

  const [submitting, setSubmitting] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState<PythonErrorFragment | null>(null);
  const [sensorExecutionData, setSensorExecutionData] =
    useState<SensorDryRunInstigationTick | null>(null);

  const sensorSelector: SensorSelector = useMemo(
    () => ({
      sensorName: name,
      repositoryLocationName: repoAddress.location,
      repositoryName: repoAddress.name,
    }),
    [repoAddress, name],
  );

  const executionParamsList = useMemo(
    () =>
      sensorExecutionData && sensorSelector
        ? buildExecutionParamsListSensor(sensorExecutionData, sensorSelector, jobName)
        : [],
    [sensorSelector, sensorExecutionData, jobName],
  );

  const submitTest = useCallback(async () => {
    setSubmitting(true);
    const result = await sensorDryRun({
      variables: {
        selectorData: sensorSelector,
        cursor,
      },
    });
    const data = result.data?.sensorDryRun;
    if (data) {
      if (data?.__typename === 'DryRunInstigationTick') {
        if (data.evaluationResult?.error) {
          setError(data.evaluationResult.error);
        } else {
          setSensorExecutionData(data);
        }
      } else if (data?.__typename === 'SensorNotFoundError') {
        showCustomAlert({
          title: 'Sensor not found',
          body: `Could not find a sensor named: ${name}`,
        });
      } else {
        setError(data);
      }
    } else {
      assertUnreachable('sensorDryRun Mutation returned no data??' as never);
    }
    setSubmitting(false);
  }, [sensorDryRun, sensorSelector, cursor, name]);

  const onCommitTickResult = useCallback(async () => {
    const cursor = sensorExecutionData?.evaluationResult?.cursor;
    if (!cursor) {
      return;
    }
    const {data} = await setCursorMutation({
      variables: {sensorSelector, cursor},
    });
    if (data?.setSensorCursor.__typename === 'Sensor') {
      await showSharedToaster({message: 'Cursor value updated', intent: 'success'});
    } else if (data?.setSensorCursor) {
      const error = data.setSensorCursor;
      await showSharedToaster({
        intent: 'danger',
        message: (
          <Group direction="row" spacing={8}>
            <div>Could not set cursor value.</div>
            <ButtonLink
              color={Colors.accentReversed()}
              underline="always"
              onClick={() => {
                showCustomAlert({
                  title: 'Python Error',
                  body:
                    error.__typename === 'PythonError' ? (
                      <PythonErrorInfo error={error} />
                    ) : (
                      'Sensor not found'
                    ),
                });
              }}
            >
              View error
            </ButtonLink>
          </Group>
        ),
      });
    }
  }, [sensorExecutionData?.evaluationResult?.cursor, sensorSelector, setCursorMutation]);

  const launchMultipleRunsWithTelemetry = useLaunchMultipleRunsWithTelemetry();

  const canLaunchAll = useMemo(() => {
    return executionParamsList != null && executionParamsList.length > 0;
  }, [executionParamsList]);

  const onLaunchAll = useCallback(async () => {
    if (!canLaunchAll) {
      return;
    }

    trackEvent('launch-all-sensor');
    setLaunching(true);

    try {
      if (executionParamsList) {
        await launchMultipleRunsWithTelemetry({executionParamsList}, 'toast');
        onCommitTickResult(); // persist tick
      }
    } catch (e) {
      console.error(e);
    }

    setLaunching(false);
    onClose();
  }, [
    canLaunchAll,
    executionParamsList,
    launchMultipleRunsWithTelemetry,
    onClose,
    onCommitTickResult,
    trackEvent,
  ]);

  const leftButtons = useMemo(() => {
    if (launching) {
      return null;
    }

    if (sensorExecutionData || error) {
      return (
        <Button
          icon={<Icon name="settings_backup_restore" />}
          data-testid={testId('try-again')}
          onClick={() => {
            setSensorExecutionData(null);
            setError(null);
          }}
        >
          Try again
        </Button>
      );
    } else {
      return null;
    }
  }, [launching, sensorExecutionData, error]);

  const rightButtons = useMemo(() => {
    if (launching) {
      return <Box flex={{direction: 'row', gap: 8}}></Box>;
    }

    if (sensorExecutionData || error) {
      const runRequests = sensorExecutionData?.evaluationResult?.runRequests;
      const numRunRequests = runRequests?.length || 0;
      const didSkip = !error && numRunRequests === 0;

      if (error) {
        return (
          <Box flex={{direction: 'row', gap: 8}}>
            <Button onClick={onClose}>Close</Button>
          </Box>
        );
      } else if (didSkip) {
        return (
          <Box flex={{direction: 'row', gap: 8}}>
            <Button onClick={onClose}>Close</Button>

            <Tooltip content="Commits tick result" placement="top-end">
              <Button
                icon={<Icon name="check_filled" />}
                intent="primary"
                onClick={onCommitTickResult}
                data-testid={testId('commit-tick-result')}
              >
                <div>Commit tick result</div>
              </Button>
            </Tooltip>
          </Box>
        );
      } else {
        return (
          <Box flex={{direction: 'row', gap: 8}}>
            <Button onClick={onClose}>Close</Button>
            <Tooltip
              canShow={!canLaunchAll || launching}
              content="Launches all runs and commits tick result"
              placement="top-end"
            >
              <Button
                icon={<Icon name="check_filled" />}
                intent="primary"
                disabled={!canLaunchAll || launching}
                onClick={onLaunchAll}
                data-testid={testId('launch-all')}
              >
                <div>Launch all & commit tick result</div>
              </Button>
            </Tooltip>
          </Box>
        );
      }
    }
    if (submitting) {
      return (
        <Box flex={{direction: 'row', gap: 8}}>
          <Button onClick={onClose}>Cancel</Button>
        </Box>
      );
    } else {
      return (
        <Box flex={{direction: 'row', gap: 8}}>
          <Button onClick={onClose}>Cancel</Button>
          <Button onClick={submitTest} intent="primary" data-testid={testId('continue')}>
            Continue
          </Button>
        </Box>
      );
    }
  }, [
    launching,
    sensorExecutionData,
    error,
    submitting,
    onClose,
    onCommitTickResult,
    canLaunchAll,
    onLaunchAll,
    submitTest,
  ]);

  const content = useMemo(() => {
    if (launching) {
      return (
        <Box flex={{direction: 'row', gap: 8, justifyContent: 'center', alignItems: 'center'}}>
          <Spinner purpose="body-text" />
          <div>Launching runs</div>
        </Box>
      );
    }
    if (sensorExecutionData || error) {
      const runRequests = sensorExecutionData?.evaluationResult?.runRequests;
      const numRunRequests = runRequests?.length || 0;
      const didSkip = !error && numRunRequests === 0;
      const dynamicPartitionRequests =
        sensorExecutionData?.evaluationResult?.dynamicPartitionsRequests;
      return (
        <Box flex={{direction: 'column', gap: 8}}>
          <Grid>
            <div>
              <Subheading>Result</Subheading>
              <Box flex={{grow: 1, alignItems: 'center'}}>
                <div>
                  {error ? (
                    <Tag intent="danger">Failed</Tag>
                  ) : numRunRequests ? (
                    <Tag intent="success">{numRunRequests} run requests</Tag>
                  ) : (
                    <Tag intent="warning">Skipped</Tag>
                  )}
                </div>
              </Box>
            </div>
            <div>
              <Subheading>Used cursor value</Subheading>
              <pre>{cursor?.length ? cursor : 'None'}</pre>
            </div>
          </Grid>
          <Box>
            {error ? (
              <div>
                <PythonErrorInfo error={error} />
              </div>
            ) : null}
            {didSkip ? (
              <Box flex={{direction: 'column', gap: 8}}>
                <Subheading style={{marginBottom: 8}}>Requested runs (0)</Subheading>
                <div>
                  <SkipReasonNonIdealStateWrapper>
                    <NonIdealState
                      icon="missing"
                      title="No runs requested"
                      description={
                        <>
                          <span>
                            The sensor function was successfully evaluated but didn&apos;t return
                            any run requests.
                          </span>
                          <span>
                            <br />
                            Skip reason:{' '}
                            {sensorExecutionData?.evaluationResult?.skipReason
                              ? `"${sensorExecutionData.evaluationResult.skipReason}"`
                              : 'No skip reason was output'}
                          </span>
                        </>
                      }
                    />
                  </SkipReasonNonIdealStateWrapper>
                </div>
              </Box>
            ) : null}
            {numRunRequests && runRequests ? (
              <Box flex={{direction: 'column', gap: 8}}>
                <Subheading>Requested runs ({numRunRequests})</Subheading>
                <RunRequestTable
                  runRequests={runRequests}
                  name={name}
                  jobName={jobName}
                  isJob={true}
                  repoAddress={repoAddress}
                />
              </Box>
            ) : null}
            {dynamicPartitionRequests?.length ? (
              <div style={{marginTop: '24px'}}>
                <DynamicPartitionRequests requests={dynamicPartitionRequests} />
              </div>
            ) : null}
          </Box>

          <ComputedCursorGrid>
            <Subheading>Computed cursor value</Subheading>
            <pre>
              {sensorExecutionData?.evaluationResult?.cursor?.length
                ? sensorExecutionData?.evaluationResult.cursor
                : error
                  ? 'Error'
                  : 'None'}
            </pre>
          </ComputedCursorGrid>
        </Box>
      );
    }
    if (submitting) {
      return (
        <Box flex={{direction: 'row', gap: 8, justifyContent: 'center', alignItems: 'center'}}>
          <Spinner purpose="body-text" />
          <div>Evaluating sensor</div>
        </Box>
      );
    } else {
      return (
        <Box flex={{direction: 'column', gap: 8}}>
          <div>Cursor value (optional)</div>
          <TextInput
            value={cursor}
            onChange={(e) => setCursor(e.target.value)}
            data-testid={testId('cursor-input')}
            placeholder="Enter a cursor value"
          />
          <div>
            A cursor tracks where a sensor left off, allowing the sensor to efficiently process new
            changes or events without missing anything or duplicating work. The cursor is typically
            a string, and can be updated within the sensor&apos;s logic to reflect the latest state.
          </div>
          <div>
            <a href="https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors#idempotence-and-cursors">
              Learn more
            </a>{' '}
            about cursors
          </div>
        </Box>
      );
    }
  }, [sensorExecutionData, error, submitting, launching, name, jobName, repoAddress, cursor]);

  return (
    <>
      <DialogBody>
        <div style={{minHeight: '300px'}}>{content}</div>
      </DialogBody>
      <DialogFooter topBorder left={leftButtons}>
        {rightButtons}
      </DialogFooter>
    </>
  );
};

export const EVALUATE_SENSOR_MUTATION = gql`
  mutation SensorDryRunMutation($selectorData: SensorSelector!, $cursor: String) {
    sensorDryRun(selectorData: $selectorData, cursor: $cursor) {
      ... on DryRunInstigationTick {
        timestamp
        evaluationResult {
          cursor
          runRequests {
            ...RunRequestFragment
          }
          skipReason
          error {
            ...PythonErrorFragment
          }
          dynamicPartitionsRequests {
            ...DynamicPartitionRequestFragment
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  fragment DynamicPartitionRequestFragment on DynamicPartitionRequest {
    partitionKeys
    partitionsDefName
    type
  }

  ${RUN_REQUEST_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  padding-bottom: 12px;
  border-bottom: 1px solid ${Colors.keylineDefault()};
  ${Subheading} {
    padding-bottom: 4px;
    display: block;
  }
  pre {
    margin: 0;
  }
  button {
    margin-top: 4px;
  }
`;

const ComputedCursorGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  padding-bottom: 12px;
  ${Subheading} {
    padding-bottom: 4px;
    display: block;
  }
  pre {
    margin: 0;
  }
  button {
    margin-top: 4px;
  }
`;

const SkipReasonNonIdealStateWrapper = styled.div`
  ${NonIdealStateWrapper} {
    margin: auto !important;
    width: unset !important;
    max-width: unset !important;
  }
`;
