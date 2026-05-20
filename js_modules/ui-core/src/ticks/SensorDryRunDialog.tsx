import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogFooter,
  Icon,
  ListItem,
  MiddleTruncate,
  NonIdealState,
  Spinner,
  Subheading,
  Tag,
  TextInput,
  Tooltip,
  showToast,
} from '@dagster-io/ui-components';
import {useCallback, useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {DynamicPartitionRequests} from './DynamicPartitionRequests';
import {RUN_REQUEST_FRAGMENT} from './RunRequestFragment';
import {gql, useMutation} from '../apollo-client';
import styles from './css/SensorDryRunDialog.module.css';
import {RunRequestFragment} from './types/RunRequestFragment.types';
import {
  SensorDryRunMutation,
  SensorDryRunMutationVariables,
} from './types/SensorDryRunDialog.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {assertUnreachable} from '../app/Util';
import {useTrackEvent} from '../app/analytics';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {DELETE_DYNAMIC_PARTITIONS_MUTATION} from '../assets/DeleteDynamicPartitionsDialog';
import {
  DeleteDynamicPartitionsMutation,
  DeleteDynamicPartitionsMutationVariables,
} from '../assets/types/DeleteDynamicPartitionsDialog.types';
import {DynamicPartitionsRequestType, SensorSelector} from '../graphql/types';
import {useLaunchMultipleRunsWithTelemetry} from '../launchpad/useLaunchMultipleRunsWithTelemetry';
import {CREATE_PARTITION_MUTATION} from '../partitions/CreatePartitionDialog';
import {
  AddDynamicPartitionMutation,
  AddDynamicPartitionMutationVariables,
} from '../partitions/types/CreatePartitionDialog.types';
import {RunConfigDialog} from '../runs/RunConfigDialog';
import {SET_CURSOR_MUTATION} from '../sensors/EditCursorDialog';
import {
  SetSensorCursorMutation,
  SetSensorCursorMutationVariables,
} from '../sensors/types/EditCursorDialog.types';
import {testId} from '../testing/testId';
import {CopyIconButton} from '../ui/CopyButton';
import {buildExecutionParamsListSensor} from '../util/buildExecutionParamsList';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

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
      style={{width: '70vw', minWidth: 500, maxWidth: 900, display: 'flex'}}
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
  const [createPartition] = useMutation<
    AddDynamicPartitionMutation,
    AddDynamicPartitionMutationVariables
  >(CREATE_PARTITION_MUTATION);
  const [deletePartition] = useMutation<
    DeleteDynamicPartitionsMutation,
    DeleteDynamicPartitionsMutationVariables
  >(DELETE_DYNAMIC_PARTITIONS_MUTATION);

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
  const dynamicPartitionRequests = sensorExecutionData?.evaluationResult?.dynamicPartitionsRequests;

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
      } else if (data?.__typename === 'UnauthorizedError') {
        showCustomAlert({
          title: 'Unauthorized',
          body: 'You do not have permission to dry run this sensor.',
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
      showToast({message: 'Tick result committed', intent: 'success'});
      onClose();
      return;
    }
    const {data} = await setCursorMutation({
      variables: {sensorSelector, cursor},
    });
    if (data?.setSensorCursor.__typename === 'Sensor') {
      showToast({message: 'Cursor value updated', intent: 'success'});
      onClose();
    } else if (data?.setSensorCursor) {
      const error = data.setSensorCursor;
      showToast({
        intent: 'danger',
        message: (
          <Box flex={{direction: 'row', gap: 8}}>
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
          </Box>
        ),
      });
    }
  }, [sensorExecutionData?.evaluationResult?.cursor, sensorSelector, setCursorMutation, onClose]);

  const launchMultipleRunsWithTelemetry = useLaunchMultipleRunsWithTelemetry();

  const canApply = useMemo(() => {
    return (
      (executionParamsList != null && executionParamsList.length > 0) ||
      (dynamicPartitionRequests?.length || 0) > 0
    );
  }, [executionParamsList, dynamicPartitionRequests]);

  const onApply = useCallback(async () => {
    if (!canApply) {
      return;
    }

    trackEvent('launch-all-sensor');
    setLaunching(true);

    try {
      if (dynamicPartitionRequests?.length) {
        await Promise.all(
          dynamicPartitionRequests.map(async (request) => {
            if (request.type === DynamicPartitionsRequestType.ADD_PARTITIONS) {
              await Promise.all(
                (request.partitionKeys || []).map(async (partitionKey) => {
                  await createPartition({
                    variables: {
                      repositorySelector: {
                        repositoryName: repoAddress.name,
                        repositoryLocationName: repoAddress.location,
                      },
                      partitionsDefName: request.partitionsDefName,
                      partitionKey,
                    },
                  });
                }),
              );
            } else if (request.partitionKeys && request.partitionKeys.length) {
              await deletePartition({
                variables: {
                  repositorySelector: {
                    repositoryName: repoAddress.name,
                    repositoryLocationName: repoAddress.location,
                  },
                  partitionsDefName: request.partitionsDefName,
                  partitionKeys: request.partitionKeys,
                },
              });
            }
          }),
        );
      }
      if (executionParamsList) {
        await launchMultipleRunsWithTelemetry({executionParamsList}, 'toast');
      }
      onCommitTickResult(); // persist tick
    } catch (e) {
      console.error(e);
    }

    setLaunching(false);
    onClose();
  }, [
    canApply,
    createPartition,
    deletePartition,
    dynamicPartitionRequests,
    executionParamsList,
    launchMultipleRunsWithTelemetry,
    onClose,
    onCommitTickResult,
    repoAddress,
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
      const hasDynamicPartitionRequests = (dynamicPartitionRequests?.length || 0) > 0;
      const didSkip = !error && numRunRequests === 0 && !hasDynamicPartitionRequests;

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
              canShow={!canApply || launching}
              content="Applies requests, launches all runs, and commits tick result"
              placement="top-end"
            >
              <Button
                icon={<Icon name="check_filled" />}
                intent="primary"
                disabled={!canApply || launching}
                onClick={onApply}
                data-testid={testId('launch-all')}
              >
                <div>Apply requests & commit tick result</div>
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
    canApply,
    onApply,
    submitTest,
    dynamicPartitionRequests?.length,
  ]);

  const content = useMemo(() => {
    if (launching) {
      return (
        <Box
          padding={{vertical: 16, horizontal: 20}}
          flex={{direction: 'row', gap: 8, justifyContent: 'center', alignItems: 'center'}}
        >
          <Spinner purpose="body-text" />
          <div>Launching runs</div>
        </Box>
      );
    }
    if (sensorExecutionData || error) {
      const runRequests = sensorExecutionData?.evaluationResult?.runRequests;
      const numRunRequests = runRequests?.length || 0;
      const dynamicPartitionRequests =
        sensorExecutionData?.evaluationResult?.dynamicPartitionsRequests;
      const hasDynamicPartitionRequests = (dynamicPartitionRequests?.length || 0) > 0;
      const didSkip = !error && numRunRequests === 0 && !hasDynamicPartitionRequests;
      return (
        <Box flex={{direction: 'column'}}>
          <Box padding={{vertical: 16, horizontal: 20}} flex={{direction: 'column', gap: 12}}>
            <Box flex={{direction: 'column', gap: 4}}>
              <label className={styles.summaryLabel}>Result</label>
              <div>
                {error ? (
                  <Tag intent="danger">Failed</Tag>
                ) : numRunRequests || hasDynamicPartitionRequests ? (
                  <Tag intent="success">
                    {[
                      numRunRequests
                        ? `${numRunRequests} run ${numRunRequests === 1 ? 'request' : 'requests'}`
                        : null,
                      hasDynamicPartitionRequests ? 'dynamic partition requests' : null,
                    ]
                      .filter(Boolean)
                      .join(', ')}
                  </Tag>
                ) : (
                  <Tag intent="warning">Skipped</Tag>
                )}
              </div>
            </Box>
            <Box flex={{direction: 'column', gap: 4}}>
              <label className={styles.summaryLabel}>Used cursor value</label>
              {cursor?.length ? <CursorValueBlock value={cursor} /> : <span>None</span>}
            </Box>
            <Box flex={{direction: 'column', gap: 4}}>
              <label className={styles.summaryLabel}>Computed cursor value</label>
              {sensorExecutionData?.evaluationResult?.cursor?.length ? (
                <CursorValueBlock value={sensorExecutionData.evaluationResult.cursor} />
              ) : (
                <span>{error ? 'Error' : 'None'}</span>
              )}
            </Box>
          </Box>
          {error ? (
            <Box padding={{horizontal: 20, bottom: 16}}>
              <PythonErrorInfo error={error} />
            </Box>
          ) : null}
          {didSkip ? (
            <Box padding={{horizontal: 20, bottom: 16}} flex={{direction: 'column', gap: 8}}>
              <Subheading style={{marginBottom: 8}}>Requested runs (0)</Subheading>
              <NonIdealState
                icon="missing"
                title="No runs requested"
                description={
                  <>
                    <span>
                      The sensor function was successfully evaluated but didn&apos;t return any run
                      requests.
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
            </Box>
          ) : null}
          {numRunRequests && runRequests ? (
            <Box flex={{direction: 'column'}}>
              <Box padding={{horizontal: 20, bottom: 12}} border="bottom">
                <Subheading>Requested runs ({numRunRequests})</Subheading>
              </Box>
              <RunRequestList
                runRequests={runRequests}
                jobName={jobName}
                repoAddress={repoAddress}
              />
            </Box>
          ) : null}
          {dynamicPartitionRequests?.length ? (
            <Box padding={{horizontal: 20, top: 16}}>
              <DynamicPartitionRequests requests={dynamicPartitionRequests} />
            </Box>
          ) : null}
        </Box>
      );
    }
    if (submitting) {
      return (
        <Box
          padding={{vertical: 16, horizontal: 20}}
          flex={{direction: 'row', gap: 8, justifyContent: 'center', alignItems: 'center'}}
        >
          <Spinner purpose="body-text" />
          <div>Evaluating sensor</div>
        </Box>
      );
    } else {
      return (
        <Box padding={{vertical: 16, horizontal: 20}} flex={{direction: 'column', gap: 8}}>
          <label className={styles.summaryLabel} htmlFor="cursor-input">
            Cursor value (optional)
          </label>
          <TextInput
            id="cursor-input"
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
  }, [sensorExecutionData, error, submitting, launching, jobName, repoAddress, cursor]);

  return (
    <>
      <div className={styles.dialogContent}>{content}</div>
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

const CursorValueBlock = ({value}: {value: string}) => (
  <div className={styles.cursorValueWrapper}>
    <pre>{value}</pre>
    <CopyIconButton value={value} iconColor={Colors.textLight()} />
  </div>
);

const RunRequestList = ({
  runRequests,
  jobName,
  repoAddress,
}: {
  runRequests: RunRequestFragment[];
  jobName: string;
  repoAddress: RepoAddress;
}) => {
  const [selectedRequest, setSelectedRequest] = useState<RunRequestFragment | null>(null);

  return (
    <>
      {runRequests.map((request, index) => {
        const pipelineName = request.jobName ?? jobName;
        const href = workspacePipelinePath({
          repoName: repoAddress.name,
          repoLocation: repoAddress.location,
          pipelineName,
          isJob: true,
        });
        return (
          <ListItem
            key={index}
            index={index}
            href={href}
            renderLink={(props) => <Link to={props.href ?? ''} {...props} />}
            padding={{vertical: 8, horizontal: 20}}
            left={
              <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                <Icon name="job" />
                <MiddleTruncate text={pipelineName} />
              </Box>
            }
            right={
              <Box padding={{left: 12}}>
                <ButtonLink
                  onClick={() => setSelectedRequest(request)}
                  data-testid={testId(`preview-${request.runKey || ''}`)}
                >
                  Preview
                </ButtonLink>
              </Box>
            }
          />
        );
      })}
      <RunConfigDialog
        isOpen={!!selectedRequest}
        onClose={() => setSelectedRequest(null)}
        mode={null}
        runConfigYaml={selectedRequest?.runConfigYaml ?? ''}
        tags={selectedRequest?.tags}
        isJob
        jobName={jobName}
        request={selectedRequest ?? undefined}
        repoAddress={repoAddress}
      />
    </>
  );
};
