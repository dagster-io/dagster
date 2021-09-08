import {gql, useLazyQuery, useMutation, useQuery} from '@apollo/client';
import {
  Checkbox,
  Intent,
  NonIdealState,
  Classes,
  Colors,
  InputGroup,
  Icon,
} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {SharedToaster} from '../app/DomUtils';
import {useFeatureFlags} from '../app/Flags';
import {filterByQuery} from '../app/GraphQueryImpl';
import {PipelineRunTag} from '../app/LocalStorage';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {LaunchButton} from '../execute/LaunchButton';
import {TagContainer, TagEditor} from '../execute/TagEditor';
import {GanttChartMode} from '../gantt/GanttChart';
import {buildLayout} from '../gantt/GanttChartLayout';
import {useViewport} from '../gantt/useViewport';
import {PipelineRunStatus} from '../types/globalTypes';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {Group} from '../ui/Group';
import {Spinner} from '../ui/Spinner';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {
  GridColumn,
  GridFloatingContainer,
  GridScrollContainer,
  LeftLabel,
  TopLabel,
  TopLabelTilted,
} from './RunMatrixUtils';
import {LaunchPartitionBackfill} from './types/LaunchPartitionBackfill';
import {PartitionStatusQuery} from './types/PartitionStatusQuery';
import {PartitionsBackfillSelectorQuery} from './types/PartitionsBackfillSelectorQuery';

const DEFAULT_RUN_LAUNCHER_NAME = 'DefaultRunLauncher';

interface BackfillOptions {
  reexecute: boolean;
  fromFailure: boolean;
}

type SelectionRange = {
  start: string;
  end: string;
};

function placeholderForPartitions(names: string[]) {
  if (names.length < 4) {
    return `ex: ${names[0]}, ${names[1]}`;
  }
  return `ex: ${names[0]}, ${names[1]}, [${names[2]}...${names[names.length - 1]}]`;
}

function partitionsToText(selected: string[], all: string[]) {
  const remaining = [...selected].sort((a, b) => all.indexOf(a) - all.indexOf(b));

  let str = '';
  while (remaining.length) {
    const start = remaining.shift()!;
    const startIdx = all.indexOf(start);
    let endIdx = startIdx;
    let endIdxInSelected = -1;
    while (
      endIdx < all.length - 1 &&
      (endIdxInSelected = remaining.indexOf(all[endIdx + 1])) !== -1
    ) {
      endIdx++;
      remaining.splice(endIdxInSelected, 1);
    }
    if (endIdx !== startIdx) {
      str += `[${start}...${all[endIdx]}], `;
    } else {
      str += `${start}, `;
    }
  }
  return str.replace(/, $/, '');
}

function textToPartitions(selected: string, all: string[]) {
  const terms = selected.split(',').map((s) => s.trim());
  const result = [];
  for (const term of terms) {
    if (term.length === 0) {
      continue;
    }
    const rangeMatch = /^\[(.*)\.\.\.(.*)\]$/g.exec(term);
    if (rangeMatch) {
      const [, start, end] = rangeMatch;
      const allStartIdx = all.indexOf(start);
      const allEndIdx = all.indexOf(end);
      if (allStartIdx === -1 || allEndIdx === -1) {
        throw new Error(`Could not find partitions for provided range: ${start}...${end}`);
      }
      result.push(...all.slice(allStartIdx, allEndIdx + 1));
    } else if (term.includes('*')) {
      const [prefix, suffix] = term.split('*');
      result.push(...all.filter((p) => p.startsWith(prefix) && p.endsWith(suffix)));
    } else {
      const idx = all.indexOf(term);
      if (idx === -1) {
        throw new Error(`Could not find partition: ${term}`);
      }
      result.push(term);
    }
  }
  return result.sort((a, b) => all.indexOf(a) - all.indexOf(b));
}

export const PartitionsBackfillPartitionSelector: React.FC<{
  partitionSetName: string;
  pipelineName: string;
  onLaunch?: (backfillId: string, stepQuery: string) => void;
  onSubmit: () => void;
  repoAddress: RepoAddress;
}> = ({partitionSetName, pipelineName, onLaunch, onSubmit, repoAddress}) => {
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
  const {flagPipelineModeTuples} = useFeatureFlags();

  const {containerProps} = useViewport({
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

  const {loading, data} = useQuery<PartitionsBackfillSelectorQuery>(
    PARTITIONS_BACKFILL_SELECTOR_QUERY,
    {
      variables: {
        repositorySelector,
        partitionSetName,
        pipelineSelector: {
          ...repositorySelector,
          pipelineName,
        },
      },
      fetchPolicy: 'network-only',
    },
  );

  const [
    queryStatuses,
    {loading: statusesLoading, data: statusesData},
  ] = useLazyQuery<PartitionStatusQuery>(PARTITION_STATUS_QUERY, {
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
      <NonIdealState
        icon={IconNames.ERROR}
        title="Partition Set Not Found"
        description={data.partitionSetOrError.message}
      />
    );
  }
  if (data.pipelineSnapshotOrError.__typename === 'PipelineNotFoundError') {
    return (
      <NonIdealState
        icon={IconNames.ERROR}
        title={flagPipelineModeTuples ? 'Job not found' : 'Pipeline not found'}
        description={data.pipelineSnapshotOrError.message}
      />
    );
  }
  if (data.pipelineSnapshotOrError.__typename === 'PipelineSnapshotNotFoundError') {
    return (
      <NonIdealState
        icon={IconNames.ERROR}
        title={flagPipelineModeTuples ? 'Job not found' : 'Pipeline not found'}
        description={data.pipelineSnapshotOrError.message}
      />
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
    SharedToaster.show({
      message: (
        <div>
          Created backfill job:{' '}
          <FilteredRunsLink href="/instance/backfills">{backfillId}</FilteredRunsLink>
        </div>
      ),
      intent: Intent.SUCCESS,
    });
    onLaunch?.(backfillId, query);
  };

  const onError = (data: LaunchPartitionBackfill | null | undefined) => {
    const result = data?.launchPartitionBackfill;
    let errors = <></>;
    if (
      result?.__typename === 'PythonError' ||
      result?.__typename === 'PartitionSetNotFoundError'
    ) {
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

    const message = (
      <Group direction="column" spacing={4}>
        <div>An unexpected error occurred. This backfill was not launched.</div>
        {errors ? (
          <ButtonLink
            color={Colors.WHITE}
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

    SharedToaster.show({
      message,
      icon: 'error',
      intent: Intent.DANGER,
    });
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
    .filter((x) => x.runStatus === PipelineRunStatus.SUCCESS)
    .map((x) => x.partitionName);

  const partitionsWithLastRunFailure = statuses
    .filter(
      (x) =>
        x.runStatus === PipelineRunStatus.FAILURE ||
        x.runStatus === PipelineRunStatus.CANCELED ||
        x.runStatus === PipelineRunStatus.CANCELING,
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

  const selectedString = partitionsToText(selected, partitionNames);

  return (
    <div>
      <div className={Classes.DIALOG_BODY}>
        <div style={{display: 'flex', alignItems: 'center', marginBottom: 4}}>
          <strong style={{display: 'block'}}>Partitions</strong>
          <Checkbox
            label="Select all"
            disabled={!selectablePartitions.length}
            style={{marginBottom: 0, marginLeft: 10}}
            checked={selected.length === selectablePartitions.length}
            onClick={() =>
              setSelected(
                selected.length === selectablePartitions.length ? [] : selectablePartitions,
              )
            }
          />
        </div>
        <InputGroup
          small
          fill
          placeholder={placeholderForPartitions(partitionNames)}
          key={selectedString}
          defaultValue={selectedString}
          onBlur={(e) => {
            try {
              setSelected(textToPartitions(e.target.value, partitionNames));
            } catch (err) {
              e.preventDefault();
              alert(err.message);
            }
          }}
        />
        <div style={{display: 'flex', marginTop: 10}}>
          <div>
            <strong style={{display: 'block', marginBottom: 4}}>Step Subset</strong>
            <GraphQueryInput
              small
              disabled={options.fromFailure}
              width={260}
              items={solids}
              value={query}
              placeholder="Type a Step Subset"
              onChange={setQuery}
            />
          </div>
          <div style={{marginLeft: 20}}>
            <strong style={{display: 'block', marginBottom: 6}}>Options</strong>
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
              >
                Re-execute from failures
                <Tooltip content="For each partition, if the most recent run failed, launch a re-execution starting from the steps that failed.">
                  <Icon
                    icon="info-sign"
                    iconSize={12}
                    color={Colors.GRAY3}
                    style={{position: 'relative', top: '-2px', marginLeft: '6px'}}
                  />
                </Tooltip>
              </Checkbox>
              {statusesLoading ? (
                <div style={{marginLeft: '8px', marginTop: '3px'}}>
                  <Spinner purpose="body-text" />
                </div>
              ) : null}
            </div>
          </div>
        </div>
        <div
          style={{
            display: 'flex',
            marginTop: 20,
            paddingTop: 20,
            borderTop: `1px solid ${Colors.LIGHT_GRAY3}`,
            justifyContent: 'space-between',
          }}
        >
          <strong style={{display: 'block', marginBottom: 4}}>Preview</strong>
          <div style={{color: Colors.GRAY3}}>Click or drag to edit selected partitions</div>
        </div>
        <div style={{display: 'flex', border: `1px solid ${Colors.LIGHT_GRAY1}`}}>
          {query && (
            <GridFloatingContainer floating={true}>
              <GridColumn disabled>
                <TopLabel></TopLabel>
                {stepRows.map((step) => (
                  <LeftLabel style={{paddingLeft: step.x}} key={step.name}>
                    {step.name}
                  </LeftLabel>
                ))}
              </GridColumn>
            </GridFloatingContainer>
          )}
          <GridScrollContainer {...containerProps}>
            <div style={{display: 'flex', paddingLeft: 10}}>
              {partitionNames.map((partitionName, idx) => (
                <GridColumn
                  key={partitionName}
                  style={{zIndex: partitionNames.length - idx, userSelect: 'none'}}
                  disabled={statusesLoading || !selectablePartitions.includes(partitionName)}
                  focused={selected.includes(partitionName)}
                  multiselectFocused={currentRangeSelection.includes(partitionName)}
                  onMouseDown={() => onPartitionMouseDown(partitionName)}
                  onMouseUp={() => onPartitionMouseUp(partitionName)}
                  onMouseOver={() => onPartitionMouseOver(partitionName)}
                >
                  <TopLabelTilted label={partitionName} />
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
            <Alert
              intent="warning"
              title="The backfill daemon is not running."
              description={
                <div>
                  See the{' '}
                  <a
                    href="https://docs.dagster.io/overview/daemon"
                    target="_blank"
                    rel="noreferrer"
                  >
                    dagster-daemon documentation
                  </a>{' '}
                  for more information on how to deploy the dagster-daemon process.
                </div>
              }
            />
          </div>
        ) : null}
        {usingDefaultRunLauncher && !instance.runQueuingSupported ? (
          <div style={{marginTop: 10}}>
            <Alert
              intent="warning"
              title={
                <div>
                  Using the default run launcher <code>{DEFAULT_RUN_LAUNCHER_NAME}</code> for
                  launching backfills without a queued run coordinator is not advised.
                </div>
              }
              description={
                <div>
                  Check your instance configuration in <code>dagster.yaml</code> to either configure{' '}
                  the{' '}
                  <a
                    href="https://docs.dagster.io/overview/pipeline-runs/run-coordinator"
                    target="_blank"
                    rel="noreferrer"
                  >
                    queued run coordinator
                  </a>{' '}
                  or to configure a run launcher more appropriate for launching a large number of
                  jobs.
                </div>
              }
            />
          </div>
        ) : null}
      </div>
      <div className={Classes.DIALOG_FOOTER}>
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'flex-end'}}>
          <TagEditor
            tagsFromSession={tags}
            onChange={setTags}
            open={tagEditorOpen}
            onRequestClose={() => setTagEditorOpen(false)}
          />
          {tags.length ? (
            <div style={{border: '1px solid #ececec', borderBottom: 'none'}}>
              <TagContainer
                tags={{fromSession: tags}}
                onRequestEdit={() => setTagEditorOpen(true)}
              />
            </div>
          ) : (
            <ButtonLink
              color="#106ba3"
              onClick={() => setTagEditorOpen(true)}
              style={{margin: '9px  9px 0 9px'}}
            >
              + Add tags to backfill runs
            </ButtonLink>
          )}
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
        </div>
      </div>
    </div>
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
  const [launchBackfill, {loading}] = useMutation<LaunchPartitionBackfill>(
    LAUNCH_PARTITION_BACKFILL_MUTATION,
  );

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
    <Box flex={{justifyContent: 'flex-end', alignItems: 'center'}} margin={{top: 12}}>
      <LaunchButton
        runCount={count}
        config={{
          title: buttonTitle,
          icon: 'send-to',
          disabled: !count || loading,
          onClick: onLaunch,
        }}
      />
    </Box>
  );
};

const FilteredRunsLink = styled.a`
  text-decoration: underline;
`;

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

const LAUNCH_PARTITION_BACKFILL_MUTATION = gql`
  mutation LaunchPartitionBackfill($backfillParams: LaunchBackfillParams!) {
    launchPartitionBackfill(backfillParams: $backfillParams) {
      __typename
      ... on LaunchBackfillSuccess {
        backfillId
      }
      ... on PartitionSetNotFoundError {
        message
      }
      ...PythonErrorFragment
      ... on InvalidStepError {
        invalidStepKey
      }
      ... on InvalidOutputError {
        stepKey
        invalidOutputName
      }
      ... on UnauthorizedError {
        message
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on PipelineRunConflict {
        message
      }
      ... on ConflictingExecutionParamsError {
        message
      }
      ... on PresetNotFoundError {
        message
      }
      ... on PipelineConfigValidationInvalid {
        pipelineName
        errors {
          __typename
          message
          path
          reason
        }
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
