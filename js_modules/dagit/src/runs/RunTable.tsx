import {gql} from '@apollo/client';
import {Checkbox, NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {PipelineSnapshotLink} from 'src/pipelines/PipelinePathUtils';
import {RunActionsMenu, RunBulkActionsMenu} from 'src/runs/RunActionsMenu';
import {RunStatusTagWithStats} from 'src/runs/RunStatusTag';
import {canceledStatuses, queuedStatuses} from 'src/runs/RunStatuses';
import {RunTags} from 'src/runs/RunTags';
import {RunElapsed, RunTime, RUN_TIME_FRAGMENT, titleForRun} from 'src/runs/RunUtils';
import {RunTableRunFragment} from 'src/runs/types/RunTableRunFragment';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Table} from 'src/ui/Table';
import {TokenizingFieldValue} from 'src/ui/TokenizingField';
import {FontFamily} from 'src/ui/styles';

interface RunTableProps {
  runs: RunTableRunFragment[];
  onSetFilter: (search: TokenizingFieldValue[]) => void;
  nonIdealState?: React.ReactNode;

  highlightedIds?: string[];
  additionalColumnHeaders?: React.ReactNode[];
  additionalColumnsForRow?: (run: RunTableRunFragment) => React.ReactNode[];
}

type State = {
  checkedRuns: Set<string>;
  lastCheckedID: string | null;
};

type Action =
  | {type: 'toggle-one'; payload: {checked: boolean; runId: string}}
  | {
      type: 'toggle-slice';
      payload: {checked: boolean; runId: string; allRuns: RunTableRunFragment[]};
    }
  | {type: 'toggle-all'; payload: {checked: boolean; allRuns: RunTableRunFragment[]}};

const reducer = (state: State, action: Action): State => {
  const copy = new Set(Array.from(state.checkedRuns));
  switch (action.type) {
    case 'toggle-one': {
      const {checked, runId} = action.payload;
      checked ? copy.add(runId) : copy.delete(runId);
      return {lastCheckedID: runId, checkedRuns: copy};
    }

    case 'toggle-slice': {
      const {checked, runId, allRuns} = action.payload;
      const {lastCheckedID} = state;

      const indexOfLast = allRuns.findIndex((run) => run.runId === lastCheckedID);
      const indexOfChecked = allRuns.findIndex((run) => run.runId === runId);
      if (indexOfLast === undefined || indexOfChecked === undefined) {
        return state;
      }

      const [start, end] = [indexOfLast, indexOfChecked].sort();
      for (let ii = start; ii <= end; ii++) {
        const runAtIndex = allRuns[ii];
        checked ? copy.add(runAtIndex.runId) : copy.delete(runAtIndex.runId);
      }

      return {
        lastCheckedID: runId,
        checkedRuns: copy,
      };
    }

    case 'toggle-all': {
      const {checked, allRuns} = action.payload;
      return {
        lastCheckedID: null,
        checkedRuns: checked ? new Set(Array.from(allRuns.map((run) => run.runId))) : new Set(),
      };
    }
  }
};

const initialState: State = {
  checkedRuns: new Set(),
  lastCheckedID: null,
};

export const RunTable = (props: RunTableProps) => {
  const {runs, onSetFilter, nonIdealState, highlightedIds} = props;
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {checkedRuns} = state;

  const onToggle = (runId: string) => (values: {checked: boolean; shiftKey: boolean}) => {
    const {checked, shiftKey} = values;
    if (shiftKey && state.lastCheckedID) {
      dispatch({type: 'toggle-slice', payload: {checked, runId, allRuns: runs}});
    } else {
      dispatch({type: 'toggle-one', payload: {checked, runId}});
    }
  };

  const toggleAll = (checked: boolean) => {
    dispatch({type: 'toggle-all', payload: {checked, allRuns: runs}});
  };

  const onChangeAll = (e: React.FormEvent<HTMLInputElement>) => {
    if (e.target instanceof HTMLInputElement) {
      toggleAll(e.target.checked);
    }
  };

  if (runs.length === 0) {
    return (
      <Box margin={{vertical: 64}}>
        {nonIdealState || (
          <NonIdealState
            icon="history"
            title="Pipeline Runs"
            description="No runs to display. Use the Playground to launch a pipeline."
          />
        )}
      </Box>
    );
  }

  const selectedFragments = runs.filter((run) => checkedRuns.has(run.runId));

  return (
    <Table>
      <thead>
        <tr>
          <th colSpan={2}>
            <div style={{display: 'flex', alignItems: 'center'}}>
              <Checkbox
                style={{marginBottom: 0, marginTop: 1}}
                indeterminate={checkedRuns.size > 0 && checkedRuns.size !== runs.length}
                checked={checkedRuns.size === runs.length}
                onChange={onChangeAll}
              />
              <RunBulkActionsMenu
                selected={selectedFragments}
                clearSelection={() => toggleAll(false)}
              />
            </div>
          </th>
          <th>Run ID</th>
          <th>Pipeline</th>
          <th style={{width: 110, minWidth: 110}}>Snapshot ID</th>
          <th style={{width: 85}}>Mode</th>
          <th style={{width: 160}}>Timing</th>
          {props.additionalColumnHeaders}
          <th style={{width: 52}} />
        </tr>
      </thead>
      <tbody>
        {runs.map((run) => (
          <RunRow
            run={run}
            key={run.runId}
            onSetFilter={onSetFilter}
            checked={checkedRuns.has(run.runId)}
            additionalColumns={props.additionalColumnsForRow?.(run)}
            onToggleChecked={onToggle(run.runId)}
            isHighlighted={highlightedIds && highlightedIds.includes(run.runId)}
          />
        ))}
      </tbody>
    </Table>
  );
};

export const RUN_TABLE_RUN_FRAGMENT = gql`
  fragment RunTableRunFragment on PipelineRun {
    id
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
    status
    tags {
      key
      value
    }
    ...RunTimeFragment
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${RUN_TIME_FRAGMENT}
`;

const RunRow: React.FC<{
  run: RunTableRunFragment;
  onSetFilter: (search: TokenizingFieldValue[]) => void;
  checked?: boolean;
  onToggleChecked?: (values: {checked: boolean; shiftKey: boolean}) => void;
  additionalColumns?: React.ReactNode[];
  isHighlighted?: boolean;
}> = ({run, onSetFilter, checked, onToggleChecked, additionalColumns, isHighlighted}) => {
  const onChange = (e: React.FormEvent<HTMLInputElement>) => {
    if (e.target instanceof HTMLInputElement) {
      const {checked} = e.target;
      const shiftKey =
        e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
      onToggleChecked && onToggleChecked({checked, shiftKey});
    }
  };

  return (
    <Row key={run.runId} highlighted={!!isHighlighted}>
      <td style={{paddingRight: '4px'}}>
        {onToggleChecked && <Checkbox checked={checked} onChange={onChange} />}
      </td>
      <td>
        <RunStatusTagWithStats status={run.status} runId={run.runId} />
      </td>
      <td style={{fontFamily: FontFamily.monospace}}>
        <Link to={`/instance/runs/${run.runId}`}>{titleForRun(run)}</Link>
      </td>
      <td>
        <Group direction="column" spacing={4}>
          <div>{run.pipelineName}</div>
          <RunTags tags={run.tags} onSetFilter={onSetFilter} />
        </Group>
      </td>
      <td>
        <PipelineSnapshotLink
          snapshotId={run.pipelineSnapshotId || ''}
          pipelineName={run.pipelineName}
        />
      </td>
      <td>
        <div>
          <div>{run.mode}</div>
        </div>
      </td>
      <td>
        <RunTime run={run} />
        {queuedStatuses.has(run.status) || canceledStatuses.has(run.status) ? null : (
          <RunElapsed run={run} />
        )}
      </td>
      {additionalColumns}
      <td>
        <RunActionsMenu run={run} />
      </td>
    </Row>
  );
};

const Row = styled.tr<{highlighted: boolean}>`
  ${({highlighted}) =>
    highlighted ? `box-shadow: inset 3px 3px #bfccd6, inset -3px -3px #bfccd6;` : null}
`;
