import {gql, useLazyQuery, useMutation, useQuery} from '@apollo/client';
import {
  Alert,
  Box,
  Button,
  ButtonLink,
  Checkbox,
  Colors,
  DialogBody,
  DialogFooter,
  Group,
  Icon,
  NonIdealState,
  Spinner,
  Tooltip,
  Mono,
} from '@dagster-io/ui';
import {History} from 'history';
import * as React from 'react';
import {useHistory} from 'react-router';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {SharedToaster} from '../app/DomUtils';
import {PipelineRunTag} from '../app/ExecutionSessionStorage';
import {filterByQuery} from '../app/GraphQueryImpl';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {GanttChartMode} from '../gantt/GanttChart';
import {buildLayout} from '../gantt/GanttChartLayout';
import {useViewport} from '../gantt/useViewport';
import {LAUNCH_PARTITION_BACKFILL_MUTATION} from '../instance/BackfillUtils';
import {
  LaunchPartitionBackfill,
  LaunchPartitionBackfillVariables,
} from '../instance/types/LaunchPartitionBackfill';
import {LaunchButton} from '../launchpad/LaunchButton';
import {TagContainer, TagEditor} from '../launchpad/TagEditor';
import {RunStatus} from '../types/globalTypes';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {PartitionRangeInput} from './PartitionRangeInput';
import {
  BOX_SIZE,
  GridColumn,
  GridFloatingContainer,
  GridScrollContainer,
  LeftLabel,
  topLabelHeightForLabels,
  TopLabel,
  TopLabelTilted,
} from './RunMatrixUtils';
import {PartitionStatusQuery, PartitionStatusQueryVariables} from './types/PartitionStatusQuery';
import {
  PartitionsBackfillSelectorQuery,
  PartitionsBackfillSelectorQueryVariables,
} from './types/PartitionsBackfillSelectorQuery';

const OVERSCROLL = 200;
const DEFAULT_RUN_LAUNCHER_NAME = 'DefaultRunLauncher';

interface BackfillOptions {
  reexecute: boolean;
  fromFailure: boolean;
}

type SelectionRange = {
  start: string;
  end: string;
};

export const PartitionsBackfillPartitionSelector: React.FC<{
  partitionSetName: string;
  pipelineName: string;
  onLaunch?: (backfillId: string, stepQuery: string) => void;
  onCancel?: () => void;
  onSubmit: () => void;
  repoAddress: RepoAddress;
}> = ({partitionSetName, pipelineName, onLaunch, onCancel, onSubmit, repoAddress}) => {
  const history = useHistory();
  const repositorySelector = repoAddressToSelector(repoAddress);
  const [currentSelectionRange, setCurrentSelectionRange] = React.useState<
    SelectionRange | undefined
  >();
  const [selected, setSelected] = React.useState<string[]>([]);
  const [tagEditorOpen, setTagEditorOpen] = React.useState<boolean>(false);
  const [tags, setTags] = React.useState<PipelineRunTag[]>([]);
  const [query, setQuery] = React.useState<string>('');
  const [options, setOptions] = React.useState<BackfillOptions>({
    reexecute: false,
    fromFailure: false,
  });

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);

  const {containerProps, viewport} = useViewport({
    initialOffset: React.useCallback((el) => ({left: el.scrollWidth - el.clientWidth, top: 0}), []),
  });

  React.useEffect(() => {
    const resetSelectionRange = () => setCurrentSelectionRange(undefined);
    window.addEventListener('mouseup', resetSelectionRange);
    return () => window.removeEventListener('mouseup', resetSelectionRange);
  });

  const mounted = React.useRef(true);
  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, [onLaunch]);

  const {loading, data} = useQuery<
    PartitionsBackfillSelectorQuery,
    PartitionsBackfillSelectorQueryVariables
  >(PARTITIONS_BACKFILL_SELECTOR_QUERY, {
    variables: {
      repositorySelector,
      partitionSetName,
      pipelineSelector: {
        ...repositorySelector,
        pipelineName,
      },
    },
    fetchPolicy: 'network-only',
  });

  const [queryStatuses, {loading: statusesLoading, data: statusesData}] = useLazyQuery<
    PartitionStatusQuery,
    PartitionStatusQueryVariables
  >(PARTITION_STATUS_QUERY, {
    variables: {
      repositorySelector,
      partitionSetName,
    },
    fetchPolicy: 'cache-and-network',
  });

  if (!data || loading) {
    return (
      <Box margin={{vertical: 32}} flex={{justifyContent: 'center'}}>
        <Spinner purpose="section" />
      </Box>
    );
  }

  if (data.partitionSetOrError.__typename === 'PartitionSetNotFoundError') {
    return (
      <Box margin={20}>
        <NonIdealState
          icon="error"
          title="Partition Set Not Found"
          description={data.partitionSetOrError.message}
        />
      </Box>
    );
  }
  if (data.pipelineSnapshotOrError.__typename === 'PipelineNotFoundError') {
    return (
      <Box margin={20}>
        <NonIdealState
          icon="error"
          title={isJob ? 'Job not found' : 'Pipeline not found'}
          description={data.pipelineSnapshotOrError.message}
        />
      </Box>
    );
  }
  if (data.pipelineSnapshotOrError.__typename === 'PipelineSnapshotNotFoundError') {
    return (
      <Box margin={20}>
        <NonIdealState
          icon="error"
          title={isJob ? 'Job not found' : 'Pipeline not found'}
          description={data.pipelineSnapshotOrError.message}
        />
      </Box>
    );
  }

  if (data.partitionSetOrError.__typename === 'PythonError') {
    return (
      <Box margin={20}>
        <PythonErrorInfo error={data.partitionSetOrError} />
      </Box>
    );
  }

  if (data.pipelineSnapshotOrError.__typename === 'PythonError') {
    return (
      <Box margin={20}>
        <PythonErrorInfo error={data.pipelineSnapshotOrError} />;
      </Box>
    );
  }

  if (statusesData?.partitionSetOrError.__typename === 'PythonError') {
    return (
      <Box margin={20}>
        <PythonErrorInfo error={statusesData?.partitionSetOrError} />
      </Box>
    );
  }

  const onSuccess = (backfillId: string) => {
    showBackfillSuccessToast(history, backfillId);
    onLaunch?.(backfillId, query);
  };

  const onError = (data: LaunchPartitionBackfill | null | undefined) => {
    showBackfillErrorToast(data);
  };

  const {
    partitionSetOrError: partitionSet,
    pipelineSnapshotOrError: pipelineSnapshot,
    instance,
  } = data;

  const solids = pipelineSnapshot.solidHandles.map((h: any) => h.solid);
  const runPartitions =
    partitionSet.partitionsOrError.__typename === 'Partitions'
      ? partitionSet.partitionsOrError.results
      : null;

  if (!solids || !runPartitions) {
    return <span />;
  }

  const partitionStatuses = () => {
    if (
      statusesData?.partitionSetOrError.__typename === 'PartitionSet' &&
      statusesData.partitionSetOrError.partitionStatusesOrError.__typename === 'PartitionStatuses'
    ) {
      return statusesData.partitionSetOrError.partitionStatusesOrError.results;
    }
    return [];
  };

  const partitionNames = runPartitions.map((x) => x.name);
  const statuses = partitionStatuses();

  const partitionsWithLastRunSuccess = statuses
    .filter((x) => x.runStatus === RunStatus.SUCCESS)
    .map((x) => x.partitionName);

  const partitionsWithLastRunFailure = statuses
    .filter(
      (x) =>
        x.runStatus === RunStatus.FAILURE ||
        x.runStatus === RunStatus.CANCELED ||
        x.runStatus === RunStatus.CANCELING,
    )
    .map((x) => x.partitionName);

  const selectablePartitions = options.reexecute
    ? options.fromFailure
      ? partitionsWithLastRunFailure
      : partitionsWithLastRunSuccess
    : partitionNames;

  const solidsFiltered = filterByQuery(solids, query);
  const layout = buildLayout({nodes: solidsFiltered.all, mode: GanttChartMode.FLAT});
  const stepRows = layout.boxes.map((box) => ({
    x: box.x,
    name: box.node.name,
  }));

  const usingDefaultRunLauncher = instance.runLauncher?.name === DEFAULT_RUN_LAUNCHER_NAME;

  const getRangeSelection = (start: string, end: string) => {
    const startIdx = selectablePartitions.indexOf(start);
    const endIdx = selectablePartitions.indexOf(end);
    return selectablePartitions.slice(Math.min(startIdx, endIdx), Math.max(startIdx, endIdx) + 1);
  };

  const currentRangeSelection = currentSelectionRange
    ? getRangeSelection(currentSelectionRange.start, currentSelectionRange.end)
    : [];

  const onPartitionMouseDown = (name: string) => {
    setCurrentSelectionRange({start: name, end: name});
  };

  const onPartitionMouseUp = (_: string) => {
    if (!currentRangeSelection.length) {
      return;
    }

    const allSelected = currentRangeSelection.every((name) => selected.includes(name));
    if (allSelected) {
      setSelected(selected.filter((x) => !currentRangeSelection.includes(x)));
    } else {
      const newSelected = new Set(selected);
      currentRangeSelection.forEach((name) => newSelected.add(name));
      setSelected(Array.from(newSelected));
    }
    setCurrentSelectionRange(undefined);
  };

  const onPartitionMouseOver = (name: string) => {
    if (!currentSelectionRange) {
      return;
    }
    const {start} = currentSelectionRange;
    setCurrentSelectionRange({start, end: name});
  };

  const visibleRangeStart = Math.max(0, Math.floor((viewport.left - OVERSCROLL) / BOX_SIZE));
  const visibleCount = Math.ceil((viewport.width + OVERSCROLL * 2) / BOX_SIZE);
  const visiblePartitionNames = partitionNames.slice(
    visibleRangeStart,
    visibleRangeStart + visibleCount,
  );

  const topLabelHeight = topLabelHeightForLabels(partitionNames);

  return (
    <>
      <DialogBody>
        <Box flex={{direction: 'column', gap: 8}}>
          <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
            <strong style={{display: 'block'}}>Partitions</strong>
            <Checkbox
              label="Select all"
              disabled={!selectablePartitions.length}
              style={{marginBottom: 0, marginLeft: 10}}
              checked={selected.length === selectablePartitions.length}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                if (!e.target.checked) {
                  setSelected([]);
                } else {
                  setSelected(
                    selected.length === selectablePartitions.length ? [] : selectablePartitions,
                  );
                }
              }}
            />
          </Box>
          <PartitionRangeInput
            value={selected}
            partitionNames={partitionNames}
            onChange={setSelected}
          />
        </Box>
        <Box flex={{direction: 'row', gap: 24}} margin={{top: 16}}>
          <Box flex={{direction: 'column', gap: 8}}>
            <strong>Step subset</strong>
            <GraphQueryInput
              disabled={options.fromFailure}
              width={520}
              items={solids}
              value={query}
              placeholder="Type a step subset"
              onChange={setQuery}
            />
          </Box>
          <Box flex={{direction: 'column', gap: 12}}>
            <strong>Options</strong>
            <div style={{display: 'flex'}}>
              <Checkbox
                checked={options.fromFailure}
                onChange={() => {
                  if (!statusesData) {
                    queryStatuses();
                  }
                  setSelected([]);
                  setQuery('');
                  setOptions({
                    ...options,
                    reexecute: !options.reexecute,
                    fromFailure: !options.fromFailure,
                  });
                }}
                label={
                  <Box flex={{display: 'inline-flex', alignItems: 'center'}}>
                    <Box margin={{right: 4}}>Re-execute from failures</Box>
                    <Tooltip
                      placement="top"
                      content="For each partition, if the most recent run failed, launch a re-execution starting from the steps that failed."
                    >
                      <Icon name="info" color={Colors.Gray500} />
                    </Tooltip>
                  </Box>
                }
              />
              {statusesLoading ? (
                <div style={{marginLeft: '8px', marginTop: '3px'}}>
                  <Spinner purpose="body-text" />
                </div>
              ) : null}
            </div>
          </Box>
        </Box>
        <Box flex={{direction: 'column', gap: 8}} margin={{top: 16}}>
          <TagEditor
            tagsFromSession={tags}
            onChange={setTags}
            open={tagEditorOpen}
            onRequestClose={() => setTagEditorOpen(false)}
          />
          <strong>Tags</strong>
          {tags.length ? (
            <div style={{border: `1px solid ${Colors.Gray300}`, borderRadius: 8, padding: 3}}>
              <TagContainer tagsFromSession={tags} onRequestEdit={() => setTagEditorOpen(true)} />
            </div>
          ) : (
            <div>
              <Button onClick={() => setTagEditorOpen(true)}>Add tags to backfill runs</Button>
            </div>
          )}
        </Box>

        <div
          style={{
            display: 'flex',
            marginTop: 20,
            paddingTop: 20,
            borderTop: `1px solid ${Colors.Gray100}`,
            justifyContent: 'space-between',
          }}
        >
          <strong style={{display: 'block', marginBottom: 4}}>Preview</strong>
          <div style={{color: Colors.Gray400}}>Click or drag to edit selected partitions</div>
        </div>
        <div style={{display: 'flex', border: `1px solid ${Colors.Gray200}`}}>
          {query && (
            <GridFloatingContainer floating={true}>
              <GridColumn disabled>
                <TopLabel style={{height: topLabelHeight}} />
                {stepRows.map((step) => (
                  <LeftLabel style={{paddingLeft: step.x}} key={step.name}>
                    {step.name}
                  </LeftLabel>
                ))}
              </GridColumn>
            </GridFloatingContainer>
          )}
          <GridScrollContainer {...containerProps}>
            <div
              style={{
                width: partitionNames.length * BOX_SIZE,
                position: 'relative',
                height: query
                  ? stepRows.length * BOX_SIZE + topLabelHeight
                  : BOX_SIZE + topLabelHeight + 25,
              }}
            >
              {visiblePartitionNames.map((partitionName, idx) => (
                <GridColumn
                  key={partitionName}
                  style={{
                    zIndex: partitionNames.length - (idx + visibleRangeStart),
                    width: BOX_SIZE,
                    position: 'absolute',
                    userSelect: 'none',
                    left: (idx + visibleRangeStart) * BOX_SIZE,
                  }}
                  disabled={statusesLoading || !selectablePartitions.includes(partitionName)}
                  focused={selected.includes(partitionName)}
                  multiselectFocused={currentRangeSelection.includes(partitionName)}
                  onMouseDown={() => onPartitionMouseDown(partitionName)}
                  onMouseUp={() => onPartitionMouseUp(partitionName)}
                  onMouseOver={() => onPartitionMouseOver(partitionName)}
                >
                  <TopLabelTilted $height={topLabelHeight} label={partitionName} />
                  {!options.reexecute ? (
                    <div
                      className={`square ${
                        selectablePartitions.includes(partitionName) ? 'missing' : 'disabled'
                      }`}
                    />
                  ) : options.fromFailure ? (
                    <div
                      className={`square ${
                        selectablePartitions.includes(partitionName) ? 'failure' : 'disabled'
                      }`}
                    />
                  ) : (
                    stepRows.map((step) => (
                      <div
                        key={`${partitionName}:${step.name}`}
                        className={`square ${
                          selectablePartitions.includes(partitionName) ? 'missing' : 'disabled'
                        }`}
                      />
                    ))
                  )}
                </GridColumn>
              ))}
            </div>
          </GridScrollContainer>
        </div>

        {!instance.daemonHealth.daemonStatus.healthy ? (
          <div style={{marginTop: 10}}>
            <DaemonNotRunningAlert />
          </div>
        ) : null}
        {usingDefaultRunLauncher && !instance.runQueuingSupported ? (
          <div style={{marginTop: 10}}>
            <UsingDefaultLauncherAlert />
          </div>
        ) : null}
      </DialogBody>
      <DialogFooter>
        <Button intent="none" onClick={onCancel}>
          Cancel
        </Button>
        <LaunchBackfillButton
          partitionNames={selected}
          partitionSetName={partitionSet.name}
          reexecutionSteps={
            !options.fromFailure && solidsFiltered.all.length < solids.length
              ? stepRows.map((step) => step.name)
              : undefined
          }
          fromFailure={options.fromFailure}
          tags={tags}
          onSubmit={onSubmit}
          onSuccess={onSuccess}
          onError={onError}
          repoAddress={repoAddress}
        />
      </DialogFooter>
    </>
  );
};

const LaunchBackfillButton: React.FC<{
  partitionSetName: string;
  partitionNames: string[];
  reexecutionSteps?: string[];
  fromFailure?: boolean;
  tags?: PipelineRunTag[];
  onSuccess?: (backfillId: string) => void;
  onError: (data: LaunchPartitionBackfill | null | undefined) => void;
  onSubmit: () => void;
  repoAddress: RepoAddress;
}> = ({
  partitionSetName,
  partitionNames,
  reexecutionSteps,
  fromFailure,
  tags,
  onSuccess,
  onError,
  onSubmit,
  repoAddress,
}) => {
  const repositorySelector = repoAddressToSelector(repoAddress);
  const mounted = React.useRef(true);
  const [launchBackfill, {loading}] = useMutation<
    LaunchPartitionBackfill,
    LaunchPartitionBackfillVariables
  >(LAUNCH_PARTITION_BACKFILL_MUTATION);

  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, [onSuccess]);

  const onLaunch = async () => {
    onSubmit();
    const {data} = await launchBackfill({
      variables: {
        backfillParams: {
          selector: {
            partitionSetName,
            repositorySelector,
          },
          partitionNames,
          reexecutionSteps,
          fromFailure,
          tags,
        },
      },
    });

    if (!mounted.current) {
      return;
    }

    if (data && data.launchPartitionBackfill.__typename === 'LaunchBackfillSuccess') {
      onSuccess?.(data.launchPartitionBackfill.backfillId);
    } else {
      onError?.(data);
    }
  };

  const count = partitionNames.length;
  const reexecutionCount = reexecutionSteps?.length;

  const title = () => {
    if (loading) {
      return `Submitting ${count} ${count === 1 ? 'run' : 'runs'}…`;
    }

    if (count) {
      return `Submit ${count} ${count === 1 ? 'run' : 'runs'}`;
    }

    return 'Select partitions to submit';
  };

  const subtitle = () => {
    return !loading && reexecutionCount
      ? `(${reexecutionCount} selected ${reexecutionCount === 1 ? 'step' : 'steps'})`
      : '';
  };

  const buttonTitle = [title(), subtitle()].join(' ');

  return (
    <LaunchButton
      runCount={count}
      config={{
        title: buttonTitle,
        icon: 'open_in_new',
        disabled: !count || loading,
        onClick: onLaunch,
      }}
    />
  );
};

const PARTITIONS_BACKFILL_SELECTOR_QUERY = gql`
  query PartitionsBackfillSelectorQuery(
    $partitionSetName: String!
    $repositorySelector: RepositorySelector!
    $pipelineSelector: PipelineSelector!
  ) {
    partitionSetOrError(
      partitionSetName: $partitionSetName
      repositorySelector: $repositorySelector
    ) {
      ... on PartitionSet {
        id
        name
        partitionsOrError {
          ... on Partitions {
            results {
              name
            }
          }
          ...PythonErrorFragment
        }
      }
      ... on PartitionSetNotFoundError {
        message
      }
      ...PythonErrorFragment
    }
    pipelineSnapshotOrError(activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
        id
        name
        solidHandles {
          handleID
          solid {
            name
            definition {
              name
            }
            inputs {
              dependsOn {
                solid {
                  name
                }
              }
            }
            outputs {
              dependedBy {
                solid {
                  name
                }
              }
            }
          }
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on PipelineSnapshotNotFoundError {
        message
      }
      ...PythonErrorFragment
    }
    instance {
      runLauncher {
        name
      }
      daemonHealth {
        id
        daemonStatus(daemonType: "BACKFILL") {
          id
          healthy
        }
      }
      runQueuingSupported
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

const PARTITION_STATUS_QUERY = gql`
  query PartitionStatusQuery($partitionSetName: String!, $repositorySelector: RepositorySelector!) {
    partitionSetOrError(
      partitionSetName: $partitionSetName
      repositorySelector: $repositorySelector
    ) {
      ... on PartitionSet {
        id
        name
        partitionStatusesOrError {
          ... on PartitionStatuses {
            results {
              id
              partitionName
              runStatus
            }
          }
          ...PythonErrorFragment
        }
      }
      ... on PartitionSetNotFoundError {
        message
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

function messageForLaunchBackfillError(data: LaunchPartitionBackfill | null | undefined) {
  const result = data?.launchPartitionBackfill;

  let errors = <></>;
  if (result?.__typename === 'PythonError' || result?.__typename === 'PartitionSetNotFoundError') {
    errors = <PythonErrorInfo error={result} />;
  } else if (result?.__typename === 'InvalidStepError') {
    errors = <div>{`Invalid step: ${result.invalidStepKey}`}</div>;
  } else if (result?.__typename === 'InvalidOutputError') {
    errors = <div>{`Invalid output: ${result.invalidOutputName} for ${result.stepKey}`}</div>;
  } else if (result && 'errors' in result) {
    errors = (
      <>
        {result['errors'].map((error, idx) => (
          <PythonErrorInfo error={error} key={idx} />
        ))}
      </>
    );
  }

  return (
    <Group direction="column" spacing={4}>
      <div>An unexpected error occurred. This backfill was not launched.</div>
      {errors ? (
        <ButtonLink
          color={Colors.White}
          underline="always"
          onClick={() => {
            showCustomAlert({
              body: errors,
            });
          }}
        >
          View error
        </ButtonLink>
      ) : null}
    </Group>
  );
}

export function showBackfillErrorToast(data: LaunchPartitionBackfill | null | undefined) {
  SharedToaster.show({
    message: messageForLaunchBackfillError(data),
    icon: 'error',
    intent: 'danger',
  });
}

export function showBackfillSuccessToast(history: History<unknown>, backfillId: string) {
  SharedToaster.show({
    intent: 'success',
    message: (
      <div>
        Created backfill <Mono>{backfillId}</Mono>
      </div>
    ),
    action: {
      text: 'View',
      onClick: () => history.push(`/instance/backfills`),
    },
  });
}

const DaemonNotRunningAlert: React.FC = () => (
  <Alert
    intent="warning"
    title="The backfill daemon is not running."
    description={
      <div>
        See the{' '}
        <a
          href="https://docs.dagster.io/deployment/dagster-daemon"
          target="_blank"
          rel="noreferrer"
        >
          dagster-daemon documentation
        </a>{' '}
        for more information on how to deploy the dagster-daemon process.
      </div>
    }
  />
);

const UsingDefaultLauncherAlert: React.FC = () => (
  <Alert
    intent="warning"
    title={
      <div>
        Using the default run launcher <code>{DEFAULT_RUN_LAUNCHER_NAME}</code> for launching
        backfills without a queued run coordinator is not advised.
      </div>
    }
    description={
      <div>
        Check your instance configuration in <code>dagster.yaml</code> to either configure the{' '}
        <a
          href="https://docs.dagster.io/deployment/run-coordinator"
          target="_blank"
          rel="noreferrer"
        >
          queued run coordinator
        </a>{' '}
        or to configure a run launcher more appropriate for launching a large number of jobs.
      </div>
    }
  />
);
