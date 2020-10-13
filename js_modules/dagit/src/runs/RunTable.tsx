import {Checkbox, NonIdealState, Tag} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {useActivePipelineForName} from 'src/DagsterRepositoryContext';
import {Legend, LegendColumn, RowColumn, RowContainer} from 'src/ListComponents';
import {explorerPathToString} from 'src/PipelinePathUtils';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {TokenizingFieldValue} from 'src/TokenizingField';
import {RunActionsMenu, RunBulkActionsMenu} from 'src/runs/RunActionsMenu';
import {RunStatusWithStats} from 'src/runs/RunStatusDots';
import {RunTag} from 'src/runs/RunTag';
import {RunComponentFragments, RunElapsed, RunTime, titleForRun} from 'src/runs/RunUtils';
import {RunTableRunFragment, RunTableRunFragment_tags} from 'src/runs/types/RunTableRunFragment';

interface RunTableProps {
  runs: RunTableRunFragment[];
  onSetFilter: (search: TokenizingFieldValue[]) => void;
  nonIdealState?: React.ReactNode;
}

interface RunTableState {
  checked: RunTableRunFragment[];
}

export class RunTable extends React.Component<RunTableProps, RunTableState> {
  static fragments = {
    RunTableRunFragment: gql`
      fragment RunTableRunFragment on PipelineRun {
        runId
        status
        stepKeysToExecute
        canTerminate
        mode
        rootRunId
        parentRunId
        pipelineSnapshotId
        pipelineName
        solidSelection
        tags {
          key
          value
        }
        ...RunTimeFragment
      }

      ${PythonErrorInfo.fragments.PythonErrorFragment}
      ${RunComponentFragments.RUN_TIME_FRAGMENT}
    `,
  };

  state: RunTableState = {
    checked: [],
  };

  render() {
    const {runs, onSetFilter, nonIdealState} = this.props;
    const {checked} = this.state;

    // This is slightly complicated because we want to be able to select runs on a
    // page of results, click "Next" and continue to select more runs. Some of the data
    // (eg: selections on previous pages) are ONLY available in the `checked` state,
    // but for runs that are on the current page we want to work with the data in `runs`
    // so it's as new as possible and we don't make requests to cancel finished runs, etc.
    //
    // Clicking the "all" checkbox adds the current page if not every run is in the
    // checked set, or empties the set completely if toggling from checked => unchecked.
    //
    const checkedIds = new Set(checked.map((c) => c.runId));
    const checkedOnPage = runs.filter((r) => checkedIds.has(r.runId));
    const checkedOffPage = checked.filter((c) => !runs.some((r) => r.runId === c.runId));
    const checkedRuns = [...checkedOnPage, ...checkedOffPage];

    if (runs.length === 0) {
      return (
        <div style={{marginTop: 100, marginBottom: 100}}>
          {nonIdealState || (
            <NonIdealState
              icon="history"
              title="Pipeline Runs"
              description="No runs to display. Use the Playground to launch a pipeline."
            />
          )}
        </div>
      );
    }
    return (
      <div>
        <Legend>
          <LegendColumn style={{paddingLeft: '3px', display: 'flex', alignItems: 'center'}}>
            <Checkbox
              style={{marginBottom: 0, marginTop: 1}}
              indeterminate={checkedRuns.length > 0 && checkedOnPage.length < runs.length}
              checked={checkedOnPage.length === runs.length}
              onClick={() =>
                this.setState({
                  checked: checkedOnPage.length < runs.length ? [...checkedOffPage, ...runs] : [],
                })
              }
            />
            <RunBulkActionsMenu
              selected={checkedRuns}
              onChangeSelection={(checked) => this.setState({checked})}
            />
          </LegendColumn>
          <LegendColumn style={{flex: 5}}></LegendColumn>
          <LegendColumn style={{maxWidth: '90px'}}>Pipeline Snapshot</LegendColumn>
          <LegendColumn style={{flex: 1}}>Execution Params</LegendColumn>
          <LegendColumn style={{maxWidth: 150}}>Timing</LegendColumn>
          <LegendColumn style={{maxWidth: 50}}></LegendColumn>
        </Legend>
        {runs.map((run) => (
          <RunRow
            run={run}
            key={run.runId}
            onSetFilter={onSetFilter}
            checked={checkedRuns.includes(run)}
            onToggleChecked={() =>
              this.setState({
                checked: checkedRuns.includes(run)
                  ? checkedRuns.filter((c) => c !== run)
                  : [...checkedRuns, run],
              })
            }
          />
        ))}
      </div>
    );
  }
}

const RunRow: React.FunctionComponent<{
  run: RunTableRunFragment;
  onSetFilter: (search: TokenizingFieldValue[]) => void;
  checked?: boolean;
  onToggleChecked?: () => void;
}> = ({run, onSetFilter, checked, onToggleChecked}) => {
  const pipelineLink = `/pipeline/${explorerPathToString({
    pipelineName: run.pipelineName,
    snapshotId: run.pipelineSnapshotId || '',
    solidsQuery: '',
    pathSolids: [],
  })}`;

  const activePipeline = useActivePipelineForName(run.pipelineName);
  const isHistorical = activePipeline?.pipelineSnapshotId !== run.pipelineSnapshotId;

  return (
    <RowContainer key={run.runId} style={{paddingRight: 3}}>
      <RowColumn
        onClick={(e) => {
          e.preventDefault();
          onToggleChecked?.();
        }}
        style={{
          maxWidth: 30,
          paddingLeft: 2,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {onToggleChecked && <Checkbox checked={checked} />}
        <RunStatusWithStats status={run.status} runId={run.runId} size={14} />
      </RowColumn>
      <RowColumn style={{maxWidth: 90, fontFamily: 'monospace'}}>
        <Link to={`${pipelineLink}runs/${run.runId}`}>{titleForRun(run)}</Link>
      </RowColumn>
      <RowColumn style={{flex: 5}}>
        {run.pipelineName}
        <RunTags tags={run.tags} onSetFilter={onSetFilter} />
      </RowColumn>
      <RowColumn style={{maxWidth: '90px'}}>
        <div>
          <div style={{fontFamily: 'monospace', marginBottom: '4px'}}>
            <Link to={pipelineLink}>{run.pipelineSnapshotId?.slice(0, 8)}</Link>
          </div>
          {isHistorical ? (
            <Tag minimal intent="warning">
              Historical
            </Tag>
          ) : null}
        </div>
      </RowColumn>
      <RowColumn>
        <div>
          <div>{`Mode: ${run.mode}`}</div>
        </div>
      </RowColumn>
      <RowColumn style={{maxWidth: 150, borderRight: 0}}>
        <RunTime run={run} />
        <RunElapsed run={run} />
      </RowColumn>
      <RowColumn style={{maxWidth: 50}}>
        <RunActionsMenu run={run} />
      </RowColumn>
    </RowContainer>
  );
};

const RunTags: React.FunctionComponent<{
  tags: RunTableRunFragment_tags[];
  onSetFilter: (search: TokenizingFieldValue[]) => void;
}> = React.memo(({tags, onSetFilter}) => {
  if (!tags.length) {
    return null;
  }
  const onClick = (tag: RunTableRunFragment_tags) => {
    onSetFilter([{token: 'tag', value: `${tag.key}=${tag.value}`}]);
  };

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        width: '100%',
        position: 'relative',
        overflow: 'hidden',
        paddingTop: 7,
      }}
    >
      {tags.map((tag, idx) => (
        <RunTag tag={tag} key={idx} onClick={onClick} />
      ))}
    </div>
  );
});
