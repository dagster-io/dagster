import {gql} from '@apollo/client';
import {Checkbox, NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {explorerPathToString} from 'src/PipelinePathUtils';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {TokenizingFieldValue} from 'src/TokenizingField';
import {RunActionsMenu, RunBulkActionsMenu} from 'src/runs/RunActionsMenu';
import {RunStatusWithStats} from 'src/runs/RunStatusDots';
import {RunTag} from 'src/runs/RunTag';
import {RunComponentFragments, RunElapsed, RunTime, titleForRun} from 'src/runs/RunUtils';
import {RunTableRunFragment, RunTableRunFragment_tags} from 'src/runs/types/RunTableRunFragment';
import {Table} from 'src/ui/Table';
import {FontFamily} from 'src/ui/styles';

interface RunTableProps {
  runs: RunTableRunFragment[];
  onSetFilter: (search: TokenizingFieldValue[]) => void;
  nonIdealState?: React.ReactNode;
}

export const RunTable = (props: RunTableProps) => {
  const {runs, onSetFilter, nonIdealState} = props;
  const [checked, setChecked] = React.useState<RunTableRunFragment[]>(() => []);

  // This is slightly complicated because we want to be able to select runs on a
  // page of results, click "Next" and continue to select more runs. Some of the data
  // (eg: selections on previous pages) are ONLY available in the `checked` state,
  // but for runs that are on the current page we want to work with the data in `runs`
  // so it's as new as possible and we don't make requests to cancel finished runs, etc.
  //
  // Clicking the "all" checkbox adds the current page if not every run is in the
  // checked set, or empties the set completely if toggling from checked => unchecked.
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
    <Table striped style={{width: '100%'}}>
      <thead>
        <tr>
          <th colSpan={3}>
            <div style={{display: 'flex', alignItems: 'center'}}>
              <Checkbox
                style={{marginBottom: 0, marginTop: 1}}
                indeterminate={checkedRuns.length > 0 && checkedOnPage.length < runs.length}
                checked={checkedOnPage.length === runs.length}
                onClick={() =>
                  setChecked(checkedOnPage.length < runs.length ? [...checkedOffPage, ...runs] : [])
                }
              />
              <RunBulkActionsMenu
                selected={checkedRuns}
                onChangeSelection={(checked) => setChecked(checked)}
              />
            </div>
          </th>
          <th style={{maxWidth: '90px'}}>Pipeline Definition</th>
          <th style={{flex: 1}}>Execution Params</th>
          <th colSpan={2}>Timing</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((run) => (
          <RunRow
            run={run}
            key={run.runId}
            onSetFilter={onSetFilter}
            checked={checkedRuns.includes(run)}
            onToggleChecked={() =>
              setChecked(
                checkedRuns.includes(run)
                  ? checkedRuns.filter((c) => c !== run)
                  : [...checkedRuns, run],
              )
            }
          />
        ))}
      </tbody>
    </Table>
  );
};

RunTable.fragments = {
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

  return (
    <tr key={run.runId}>
      <td
        onClick={(e) => {
          e.preventDefault();
          onToggleChecked?.();
        }}
        style={{maxWidth: '36px'}}
      >
        {onToggleChecked && <Checkbox checked={checked} />}
        <RunStatusWithStats status={run.status} runId={run.runId} size={14} />
      </td>
      <td style={{width: '90px', fontFamily: FontFamily.monospace}}>
        <Link to={`${pipelineLink}runs/${run.runId}`}>{titleForRun(run)}</Link>
      </td>
      <td style={{width: '100%'}}>
        {run.pipelineName}
        <RunTags tags={run.tags} onSetFilter={onSetFilter} />
      </td>
      <td style={{width: '90px'}}>
        <div style={{fontFamily: FontFamily.monospace}}>
          <Link to={pipelineLink}>{run.pipelineSnapshotId?.slice(0, 8)}</Link>
        </div>
      </td>
      <td>
        <div>
          <div>{`Mode: ${run.mode}`}</div>
        </div>
      </td>
      <td style={{maxWidth: '150px'}}>
        <RunTime run={run} />
        <RunElapsed run={run} />
      </td>
      <td style={{maxWidth: '52px'}}>
        <RunActionsMenu run={run} />
      </td>
    </tr>
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
