import {Callout, Checkbox, Intent, NonIdealState, ProgressBar, TextArea} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import gql from 'graphql-tag';
import * as React from 'react';
import {useMutation, useQuery} from 'react-apollo';

import {ButtonLink} from 'src/ButtonLink';
import {useRepositorySelector} from 'src/DagsterRepositoryContext';
import {SharedToaster} from 'src/DomUtils';
import {filterByQuery} from 'src/GraphQueryImpl';
import {GraphQueryInput} from 'src/GraphQueryInput';
import {PipelineRunTag} from 'src/LocalStorage';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
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

export const PartitionsBackfillPartitionSelector: React.FunctionComponent<{
  partitionSetName: string;
  pipelineName: string;
  onLaunch?: (backfillId: string) => void;
}> = ({partitionSetName, pipelineName, onLaunch}) => {
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

  if (!data || loading) {
    return (
      <div style={{maxWidth: 600, margin: '40px auto'}}>
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

  const selectedString = partitionsToText(selected, partitionNames);

  return (
    <div style={{marginBottom: 20, padding: 10, border: '5px solid antiquewhite'}}>
      {usingDefaultRunLauncher && (
        <div style={{marginBottom: 10}}>
          <Callout intent={Intent.WARNING}>
            Using the default run launcher <code>{DEFAULT_RUN_LAUNCHER_NAME}</code> for launching
            backfills is not advised, as queueing runs is not currently supported. Check your
            instance configuration in <code>dagster.yaml</code> to configure a run launcher more
            appropriate for launching a large number of jobs.
          </Callout>
        </div>
      )}

      <h3>Launch Partition Backfill</h3>
      <div style={{display: 'flex', alignItems: 'center', marginBottom: 4}}>
        <strong style={{display: 'block'}}>Partitions</strong>
        <Checkbox
          label="Select All"
          disabled={!selectablePartitions.length}
          style={{marginBottom: 0, marginLeft: 10}}
          checked={selected.length === selectablePartitions.length}
          onClick={() =>
            setSelected(selected.length === selectablePartitions.length ? [] : selectablePartitions)
          }
        />
      </div>
      <TextArea
        growVertically
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
          <strong style={{display: 'block', marginBottom: 4}}>Options</strong>
          <div style={{display: 'flex'}}>
            <Checkbox
              label="Re-execute From Last Run"
              disabled={partitionsWithLastRunSuccess.length === 0}
              checked={options.reexecute}
              onChange={() => {
                setSelected([]);
                setQuery('');
                setOptions(
                  options.reexecute
                    ? {...options, reexecute: false, fromFailure: false}
                    : {...options, reexecute: true},
                );
              }}
            />
            <div style={{width: 20}} />
            <Checkbox
              label="Re-execute From Failure"
              checked={options.fromFailure}
              disabled={partitionsWithLastRunFailure.length === 0 || !options.reexecute}
              onChange={() => {
                setSelected([]);
                setQuery('');
                setOptions({...options, reexecute: true, fromFailure: !options.fromFailure});
              }}
            />
          </div>
        </div>
        <div style={{marginLeft: 20}}>
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
      </div>

      <div style={{display: 'flex', marginTop: 10, justifyContent: 'space-between'}}>
        <strong style={{display: 'block', marginBottom: 4}}>Preview</strong>
        <div style={{opacity: 0.5}}>Click or drag to edit selected partitions</div>
      </div>
      <div style={{display: 'flex'}}>
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
      <div style={{display: 'flex', alignItems: 'center', justifyContent: 'flex-end'}}>
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
          <ButtonLink onClick={() => setTagEditorOpen(true)} style={{margin: '9px  9px 0 9px'}}>
            + Add tags to backfill runs
          </ButtonLink>
        )}
        <LaunchBackfillButton
          partitionNames={selected}
          partitionSetName={partitionSet.name}
          reexecutionSteps={
            !options.fromFailure ? stepRows.map((step) => `${step.name}.compute`) : undefined
          }
          fromFailure={options.fromFailure}
          tags={tags}
          onSuccess={onSuccess}
        />
      </div>
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
        marginTop: 10,
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
