import {gql, useMutation} from '@apollo/client';
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
  Spinner,
  Subheading,
  Tag,
  TextInput,
} from '@dagster-io/ui-components';
import React from 'react';
import styled from 'styled-components';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {showSharedToaster} from '../app/DomUtils';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {assertUnreachable} from '../app/Util';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {SET_CURSOR_MUTATION} from '../sensors/EditCursorDialog';
import {
  SetSensorCursorMutation,
  SetSensorCursorMutationVariables,
} from '../sensors/types/EditCursorDialog.types';
import {testId} from '../testing/testId';
import {RepoAddress} from '../workspace/types';

import {RunRequestTable} from './DryRunRequestTable';
import {DynamicPartitionRequests} from './DynamicPartitionRequests';
import {RUN_REQUEST_FRAGMENT} from './RunRequestFragment';
import {
  SensorDryRunMutation,
  SensorDryRunMutationVariables,
} from './types/SensorDryRunDialog.types';

type DryRunInstigationTick = Extract<
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
      icon="sensors"
      title={name}
    >
      <SensorDryRun {...props} />
    </Dialog>
  );
};

const SensorDryRun = ({repoAddress, name, currentCursor, onClose, jobName}: Props) => {
  const [sensorDryRun] = useMutation<SensorDryRunMutation, SensorDryRunMutationVariables>(
    EVALUATE_SENSOR_MUTATION,
  );

  const [cursor, setCursor] = React.useState(currentCursor);

  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<PythonErrorFragment | null>(null);
  const [sensorExecutionData, setSensorExecutionData] =
    React.useState<DryRunInstigationTick | null>(null);

  const sensorSelector = React.useMemo(
    () => ({
      sensorName: name,
      repositoryLocationName: repoAddress.location,
      repositoryName: repoAddress.name,
    }),
    [repoAddress, name],
  );

  const submitTest = React.useCallback(async () => {
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

  const buttons = React.useMemo(() => {
    if (sensorExecutionData || error) {
      return (
        <Box flex={{direction: 'row', gap: 8}}>
          <Button
            data-testid={testId('test-again')}
            onClick={() => {
              setSensorExecutionData(null);
              setError(null);
            }}
          >
            Test again
          </Button>
          <Button intent="primary" onClick={onClose}>
            Close
          </Button>
        </Box>
      );
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
          <Button onClick={submitTest} intent="primary" data-testid={testId('evaluate')}>
            Evaluate
          </Button>
        </Box>
      );
    }
  }, [sensorExecutionData, error, submitting, onClose, submitTest]);

  const [cursorState, setCursorState] = React.useState<'Unpersisted' | 'Persisting' | 'Persisted'>(
    'Unpersisted',
  );
  const [setCursorMutation] = useMutation<
    SetSensorCursorMutation,
    SetSensorCursorMutationVariables
  >(SET_CURSOR_MUTATION);

  const onPersistCursorValue = React.useCallback(async () => {
    const cursor = sensorExecutionData?.evaluationResult?.cursor;
    if (!cursor) {
      assertUnreachable('Did not expect to get here' as never);
    }
    setCursorState('Persisting');
    const {data} = await setCursorMutation({
      variables: {sensorSelector, cursor},
    });
    if (data?.setSensorCursor.__typename === 'Sensor') {
      await showSharedToaster({message: 'Cursor value updated', intent: 'success'});
      setCursorState('Persisted');
    } else if (data?.setSensorCursor) {
      const error = data.setSensorCursor;
      await showSharedToaster({
        intent: 'danger',
        message: (
          <Group direction="row" spacing={8}>
            <div>Could not set cursor value.</div>
            <ButtonLink
              color={Colors.White}
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

  const content = React.useMemo(() => {
    if (sensorExecutionData || error) {
      const runRequests = sensorExecutionData?.evaluationResult?.runRequests;
      const numRunRequests = runRequests?.length || 0;
      const didSkip = !error && numRunRequests === 0;
      const dynamicPartitionRequests =
        sensorExecutionData?.evaluationResult?.dynamicPartitionsRequests;
      return (
        <Box flex={{direction: 'column', gap: 8}}>
          <Box>
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
              <div>
                <Subheading>Computed cursor value</Subheading>
                <pre>
                  {sensorExecutionData?.evaluationResult?.cursor?.length
                    ? sensorExecutionData?.evaluationResult.cursor
                    : error
                    ? 'Error'
                    : 'None'}
                </pre>
                {error ||
                (currentCursor ?? '') ===
                  (sensorExecutionData?.evaluationResult?.cursor ?? '') ? null : (
                  <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                    <Button
                      disabled={['Persisting', 'Persisted'].includes(cursorState)}
                      loading={cursorState === 'Persisting'}
                      onClick={onPersistCursorValue}
                    >
                      <span data-testid={testId('persist-cursor')}>
                        {cursorState === 'Persisting'
                          ? 'Persisting'
                          : cursorState === 'Persisted'
                          ? 'Persisted'
                          : 'Persist computed cursor value'}
                      </span>
                    </Button>
                    {cursorState === 'Persisted' ? (
                      <Icon name="check_circle" color={Colors.Green500} />
                    ) : null}
                  </Box>
                )}
              </div>
            </Grid>
            {error ? (
              <div>
                <PythonErrorInfo error={error} />
              </div>
            ) : null}
            {didSkip ? (
              <div>
                <Subheading>Skip reason</Subheading>
                <div>
                  {sensorExecutionData?.evaluationResult?.skipReason || 'No skip reason was output'}
                </div>
              </div>
            ) : null}
            {numRunRequests && runRequests ? (
              <RunRequestTable
                runRequests={runRequests}
                name={name}
                jobName={jobName}
                isJob={true}
                repoAddress={repoAddress}
              />
            ) : null}
            {dynamicPartitionRequests?.length ? (
              <div style={{marginTop: '24px'}}>
                <DynamicPartitionRequests requests={dynamicPartitionRequests} />
              </div>
            ) : null}
          </Box>
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
          <div>Cursor</div>
          <TextInput
            value={cursor}
            onChange={(e) => setCursor(e.target.value)}
            data-testid={testId('cursor-input')}
          />
          {currentCursor === '' || !currentCursor ? (
            <Box padding={{top: 16, bottom: 32}} flex={{justifyContent: 'center'}}>
              <NonIdealState
                icon="no-results"
                title="You're not using a cursor"
                description={
                  <span>
                    Check our{' '}
                    <a href="https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors#idempotence-and-cursors">
                      sensor documentation
                    </a>{' '}
                    to learn how to use cursors
                  </span>
                }
              />
            </Box>
          ) : null}
        </Box>
      );
    }
  }, [
    sensorExecutionData,
    error,
    submitting,
    currentCursor,
    cursorState,
    onPersistCursorValue,
    name,
    jobName,
    repoAddress,
    cursor,
  ]);

  return (
    <>
      <DialogBody>
        <div style={{minHeight: '300px'}}>{content}</div>
      </DialogBody>
      <DialogFooter topBorder>{buttons}</DialogFooter>
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
  grid-template-columns: repeat(3, 1fr);
  padding-bottom: 12px;
  border-bottom: 1px solid ${Colors.KeylineGray};
  margin-bottom: 12px;
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
