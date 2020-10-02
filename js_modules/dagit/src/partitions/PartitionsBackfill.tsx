import {
  Callout,
  Checkbox,
  Divider,
  Icon,
  Intent,
  NonIdealState,
  ProgressBar,
} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import gql from 'graphql-tag';
import * as React from 'react';
import {useMutation, useQuery} from 'react-apollo';

import {ButtonLink} from 'src/ButtonLink';
import {useRepositorySelector} from 'src/DagsterRepositoryContext';
import {SharedToaster} from 'src/DomUtils';
import {filterByQuery} from 'src/GraphQueryImpl';
import {GraphQueryInput} from 'src/GraphQueryInput';
import {Header} from 'src/ListComponents';
import {PipelineRunTag} from 'src/LocalStorage';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {OptionsDivider} from 'src/VizComponents';
import {LaunchButton} from 'src/execute/LaunchButton';
import {TagContainer, TagEditor} from 'src/execute/TagEditor';
import {GaantChartMode} from 'src/gaant/GaantChart';
import {buildLayout} from 'src/gaant/GaantChartLayout';
import {
  GridColumn,
  GridFloatingContainer,
  GridScrollContainer,
  LeftLabel,
  TopLabel,
  TopLabelTilted,
} from 'src/partitions/RunMatrixUtils';
import {PartitionsBackfillSelectorQuery} from 'src/partitions/types/PartitionsBackfillSelectorQuery';
import {PipelineRunStatus} from 'src/types/globalTypes';

const DEFAULT_RUN_LAUNCHER_NAME = 'DefaultRunLauncher';

interface BackfillOptions {
  reexecute: boolean;
  fromFailure: boolean;
}

export const PartitionsBackfill: React.FunctionComponent<{
  partitionSetName: string;
  pipelineName: string;
  showLoader: boolean;
  onLaunch?: (backfillId: string) => void;
}> = ({partitionSetName, pipelineName, showLoader, onLaunch}) => {
  const [isOpen, setOpen] = React.useState<boolean>(false);
  return (
    <div
      style={{
        marginTop: 30,
        marginBottom: 30,
        paddingBottom: 10,
      }}
    >
      <Header>Launch Partition Backfill</Header>
      <Divider />
      {isOpen ? (
        <PartitionsBackfillPartitionSelector
          partitionSetName={partitionSetName}
          pipelineName={pipelineName}
          showLoader={showLoader}
          onLaunch={(backfillId: string) => {
            onLaunch?.(backfillId);
            setOpen(false);
          }}
        />
      ) : (
        <ButtonLink onClick={() => setOpen(true)} style={{margin: 10}}>
          <Icon icon={IconNames.ADD} style={{marginRight: 10}} />
          Launch a partition backfill
        </ButtonLink>
      )}
    </div>
  );
};

type SelectionRange = {
  start: string;
  end: string;
};

export const PartitionsBackfillPartitionSelector: React.FunctionComponent<{
  partitionSetName: string;
  pipelineName: string;
  showLoader: boolean;
  onLaunch?: (backfillId: string) => void;
}> = ({partitionSetName, pipelineName, showLoader, onLaunch}) => {
  const repositorySelector = useRepositorySelector();
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

  if ((!data || loading) && showLoader) {
    return (
      <div
        style={{
          maxWidth: 600,
          margin: '40px auto',
        }}
      >
        <ProgressBar />
      </div>
    );
  }

  if (!data || loading) {
    return <div />;
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

  if (
    data.partitionSetOrError.__typename !== 'PartitionSet' ||
    data.pipelineSnapshotOrError.__typename !== 'PipelineSnapshot'
  ) {
    return <div />;
  }

  const onSuccess = (backfillId: string) => {
    SharedToaster.show({
      message: `Created backfill job "${backfillId}"`,
      intent: Intent.SUCCESS,
    });
    onLaunch?.(backfillId);
  };

  const {
    partitionSetOrError: partitionSet,
    pipelineSnapshotOrError: pipelineSnapshot,
    instance,
  } = data;

  const solids = pipelineSnapshot.solidHandles.map((h: any) => h.solid);
  const runPartitions =
    partitionSet.partitionsOrError.__typename === 'Partitions' &&
    partitionSet.partitionsOrError.results;

  if (!solids || !runPartitions) {
    return <span />;
  }
  const partitionNames = runPartitions.map((x) => x.name);
  const partitionsWithLastRunSuccess = runPartitions
    .filter((x) => x.runs.length && x.runs[0].status === PipelineRunStatus.SUCCESS)
    .map((x) => x.name);
  const partitionsWithLastRunFailure = runPartitions
    .filter((x) => x.runs.length && x.runs[0].status === PipelineRunStatus.FAILURE)
    .map((x) => x.name);
  const selectablePartitions = options.reexecute
    ? options.fromFailure
      ? partitionsWithLastRunFailure
      : partitionsWithLastRunSuccess
    : partitionNames;
  const solidsFiltered = filterByQuery(solids, query);
  const layout = buildLayout({nodes: solidsFiltered.all, mode: GaantChartMode.FLAT});
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

  return (
    <div style={{marginTop: 20}}>
      {usingDefaultRunLauncher ? (
        <div style={{marginBottom: 10}}>
          <Callout intent={Intent.WARNING}>
            Using the default run launcher <code>{DEFAULT_RUN_LAUNCHER_NAME}</code> for launching
            backfills is not advised, as queueing runs is not currently supported. Check your
            instance configuration in <code>dagster.yaml</code> to configure a run launcher more
            appropriate for launching a large number of jobs.
          </Callout>
        </div>
      ) : null}
      <div style={{display: 'flex', marginBottom: 10}}>
        <strong>Partition Backfill Selector</strong>
        <div style={{width: 20}} />
        <Checkbox
          label="Select All Partitions"
          disabled={!selectablePartitions.length}
          style={{marginBottom: 0, marginTop: 1}}
          checked={selected.length === selectablePartitions.length}
          onClick={() =>
            setSelected(selected.length === selectablePartitions.length ? [] : selectablePartitions)
          }
        />
        <div style={{width: 10}} />
        {partitionsWithLastRunSuccess.length || partitionsWithLastRunFailure.length ? (
          <OptionsDivider />
        ) : null}
        {partitionsWithLastRunSuccess.length ? (
          <>
            <div style={{width: 10}} />
            <Checkbox
              label="Re-execute From Last Run"
              checked={options.reexecute}
              onChange={() => {
                setSelected([]);
                setOptions({...options, reexecute: !options.reexecute});
              }}
            />
          </>
        ) : null}
        {partitionsWithLastRunFailure.length ? (
          <>
            <div style={{width: 20}} />
            <Checkbox
              label="Re-execute From Failure"
              checked={
                (options.reexecute || !partitionsWithLastRunSuccess.length) && options.fromFailure
              }
              disabled={!!partitionsWithLastRunSuccess.length && !options.reexecute}
              onChange={() => {
                setSelected([]);
                setOptions({...options, fromFailure: !options.fromFailure});
              }}
            />
          </>
        ) : null}
      </div>

      <TagEditor
        tags={tags}
        onChange={setTags}
        open={tagEditorOpen}
        onRequestClose={() => setTagEditorOpen(false)}
      />
      {tags.length ? (
        <div style={{border: '1px solid #ececec', borderBottom: 'none'}}>
          <TagContainer tags={tags} onRequestEdit={() => setTagEditorOpen(true)} />
        </div>
      ) : (
        <ButtonLink onClick={() => setTagEditorOpen(true)} style={{margin: '0 10px 10px'}}>
          + Add tags to backfill runs
        </ButtonLink>
      )}
      <div style={{display: 'flex'}}>
        <GridFloatingContainer floating={true}>
          <GridColumn disabled>
            {options.reexecute && !options.fromFailure ? (
              <>
                <TopLabel>
                  <GraphQueryInput
                    small
                    width={260}
                    items={solids}
                    value={query}
                    placeholder="Type a Step Subset"
                    onChange={setQuery}
                  />
                </TopLabel>
                {stepRows.map((step) => (
                  <LeftLabel style={{paddingLeft: step.x}} key={step.name}>
                    {step.name}
                  </LeftLabel>
                ))}
              </>
            ) : (
              <>
                <TopLabel></TopLabel>
                <LeftLabel>{pipelineSnapshot.name}</LeftLabel>
              </>
            )}
          </GridColumn>
        </GridFloatingContainer>

        <GridScrollContainer>
          <div style={{display: 'flex', paddingLeft: 10}}>
            {partitionNames.map((partitionName, idx) => (
              <GridColumn
                key={partitionName}
                style={{zIndex: partitionNames.length - idx, userSelect: 'none'}}
                disabled={!selectablePartitions.includes(partitionName)}
                focused={selected.includes(partitionName)}
                multiselectFocused={currentRangeSelection.includes(partitionName)}
                onMouseDown={() => onPartitionMouseDown(partitionName)}
                onMouseUp={() => onPartitionMouseUp(partitionName)}
                onMouseOver={() => onPartitionMouseOver(partitionName)}
              >
                <TopLabelTilted>
                  <div className="tilted">{partitionName}</div>
                </TopLabelTilted>
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

      {stepRows.length === 0 && (
        <div style={{padding: 20, textAlign: 'center'}}>No data to display.</div>
      )}

      <LaunchBackfillButton
        partitionNames={selected}
        partitionSetName={partitionSet.name}
        reexecutionSteps={
          options.reexecute && !options.fromFailure
            ? stepRows.map((step) => `${step.name}.compute`)
            : undefined
        }
        fromFailure={options.reexecute && options.fromFailure}
        tags={tags}
        onSuccess={onSuccess}
      />
    </div>
  );
};

const LaunchBackfillButton: React.FunctionComponent<{
  partitionSetName: string;
  partitionNames: string[];
  reexecutionSteps?: string[];
  fromFailure?: boolean;
  tags?: PipelineRunTag[];
  onSuccess?: (backfillId: string) => void;
  onError?: () => void;
}> = ({
  partitionSetName,
  partitionNames,
  reexecutionSteps,
  fromFailure,
  tags,
  onSuccess,
  onError,
}) => {
  const repositorySelector = useRepositorySelector();
  const mounted = React.useRef(true);
  const [launchBackfill] = useMutation(LAUNCH_PARTITION_BACKFILL_MUTATION);
  React.useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, [onSuccess]);
  const onLaunch = async () => {
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

    if (data && data.launchPartitionBackfill.__typename === 'PartitionBackfillSuccess') {
      onSuccess?.(data.launchPartitionBackfill.backfillId);
    } else {
      onError?.();
    }
  };

  const title = partitionNames.length
    ? partitionNames.length === 1
      ? 'Launch 1 run'
      : `Launch ${partitionNames.length} runs`
    : 'Launch';
  const subtitle = reexecutionSteps
    ? reexecutionSteps.length === 1
      ? ' (1 selected step)'
      : ` (${reexecutionSteps.length} selected steps)`
    : '';
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'flex-end',
        alignItems: 'center',
        margin: '20px 0',
      }}
    >
      <LaunchButton
        config={{
          title: `${title}${subtitle}`,
          icon: 'send-to',
          disabled: !partitionNames.length,
          tooltip: partitionNames.length
            ? partitionNames.length === 1
              ? 'Launch 1 run'
              : `Launch ${partitionNames.length} runs`
            : 'Select runs to launch',
          onClick: onLaunch,
        }}
      />
    </div>
  );
};

export const PARTITIONS_BACKFILL_SELECTOR_QUERY = gql`
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
        partitionsOrError {
          ... on Partitions {
            results {
              name
              runs(limit: 1) {
                runId
                status
              }
            }
          }
          ... on PythonError {
            ...PythonErrorFragment
          }
        }
        name
      }
      ... on PartitionSetNotFoundError {
        message
      }
      ... on PythonError {
        message
        stack
      }
    }
    pipelineSnapshotOrError(activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
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
    }
    instance {
      runLauncher {
        name
      }
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
`;

export const LAUNCH_PARTITION_BACKFILL_MUTATION = gql`
  mutation LaunchPartitionBackfill($backfillParams: PartitionBackfillParams!) {
    launchPartitionBackfill(backfillParams: $backfillParams) {
      __typename
      ... on PartitionBackfillSuccess {
        backfillId
      }
      ... on PartitionSetNotFoundError {
        message
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
`;
