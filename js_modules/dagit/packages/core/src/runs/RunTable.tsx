import {gql} from '@apollo/client';
import {Box, Checkbox, Colors, Icon, NonIdealState, Table, Mono} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {usePermissions} from '../app/Permissions';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {PipelineSnapshotLink} from '../pipelines/PipelinePathUtils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {RunsFilter} from '../types/globalTypes';
import {
  findRepositoryAmongOptions,
  isThisThingAJob,
  useRepositoryOptions,
} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {useRepositoryForRun} from '../workspace/useRepositoryForRun';
import {workspacePipelinePath, workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

import {RunActionsMenu, RunBulkActionsMenu} from './RunActionsMenu';
import {RunAssetKeyTags} from './RunAssetKeyTags';
import {RunStatusTagWithStats} from './RunStatusTag';
import {RunTags} from './RunTags';
import {
  assetKeysForRun,
  RunStateSummary,
  RunTime,
  RUN_TIME_FRAGMENT,
  titleForRun,
} from './RunUtils';
import {RunFilterToken} from './RunsFilterInput';
import {RunTableRunFragment} from './types/RunTableRunFragment';

interface RunTableProps {
  runs: RunTableRunFragment[];
  filter?: RunsFilter;
  onAddTag?: (token: RunFilterToken) => void;
  nonIdealState?: React.ReactNode;
  actionBarComponents?: React.ReactNode;
  highlightedIds?: string[];
  additionalColumnHeaders?: React.ReactNode[];
  additionalColumnsForRow?: (run: RunTableRunFragment) => React.ReactNode[];
}

export const RunTable = (props: RunTableProps) => {
  const {runs, filter, onAddTag, nonIdealState, highlightedIds, actionBarComponents} = props;
  const allIds = runs.map((r) => r.runId);

  const [{checkedIds}, {onToggleFactory, onToggleAll}] = useSelectionReducer(allIds);

  const {canTerminatePipelineExecution, canDeletePipelineRun} = usePermissions();
  const canTerminateOrDelete =
    canTerminatePipelineExecution.enabled || canDeletePipelineRun.enabled;

  const {options} = useRepositoryOptions();

  if (runs.length === 0) {
    const anyFilter = Object.keys(filter || {}).length;
    return (
      <div>
        {actionBarComponents ? (
          <Box padding={{vertical: 8, left: 24, right: 12}}>{actionBarComponents}</Box>
        ) : null}
        <Box margin={{vertical: 32}}>
          {nonIdealState || (
            <NonIdealState
              icon="run"
              title={anyFilter ? 'No matching runs' : 'No runs to display'}
              description={
                anyFilter
                  ? 'No runs were found for this filter.'
                  : 'Use the Launchpad to launch a run.'
              }
            />
          )}
        </Box>
      </div>
    );
  }

  let anyPipelines = false;
  for (const run of runs) {
    const {repositoryOrigin} = run;
    if (repositoryOrigin) {
      const repoAddress = buildRepoAddress(
        repositoryOrigin.repositoryName,
        repositoryOrigin.repositoryLocationName,
      );
      const repo = findRepositoryAmongOptions(options, repoAddress);
      if (!repo || !isThisThingAJob(repo, run.pipelineName)) {
        anyPipelines = true;
        break;
      }
    }
  }

  const selectedFragments = runs.filter((run) => checkedIds.has(run.runId));

  return (
    <>
      <Box flex={{alignItems: 'center', gap: 12}} padding={{vertical: 8, left: 24, right: 12}}>
        {actionBarComponents}
        <div style={{flex: 1}} />
        <RunBulkActionsMenu
          selected={selectedFragments}
          clearSelection={() => onToggleAll(false)}
        />
      </Box>

      <Table>
        <thead>
          <tr>
            <th style={{width: 42, paddingTop: 0, paddingBottom: 0}}>
              {canTerminateOrDelete ? (
                <Checkbox
                  indeterminate={checkedIds.size > 0 && checkedIds.size !== runs.length}
                  checked={checkedIds.size === runs.length}
                  onChange={(e: React.FormEvent<HTMLInputElement>) => {
                    if (e.target instanceof HTMLInputElement) {
                      onToggleAll(e.target.checked);
                    }
                  }}
                />
              ) : null}
            </th>
            <th style={{width: 120}}>Status</th>
            <th style={{width: 90}}>Run ID</th>
            <th>{anyPipelines ? 'Job / Pipeline' : 'Job'}</th>
            <th style={{width: 90}}>Snapshot ID</th>
            <th style={{width: 190}}>Timing</th>
            {props.additionalColumnHeaders}
            <th style={{width: 52}} />
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <RunRow
              canTerminateOrDelete={canTerminateOrDelete}
              run={run}
              key={run.runId}
              onAddTag={onAddTag}
              checked={checkedIds.has(run.runId)}
              additionalColumns={props.additionalColumnsForRow?.(run)}
              onToggleChecked={onToggleFactory(run.runId)}
              isHighlighted={highlightedIds && highlightedIds.includes(run.runId)}
            />
          ))}
        </tbody>
      </Table>
    </>
  );
};

export const RUN_TABLE_RUN_FRAGMENT = gql`
  fragment RunTableRunFragment on Run {
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
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
    solidSelection
    assetSelection {
      ... on AssetKey {
        path
      }
    }
    status
    tags {
      key
      value
    }
    ...RunTimeFragment
  }

  ${RUN_TIME_FRAGMENT}
`;

const RunRow: React.FC<{
  run: RunTableRunFragment;
  canTerminateOrDelete: boolean;
  onAddTag?: (token: RunFilterToken) => void;
  checked?: boolean;
  onToggleChecked?: (values: {checked: boolean; shiftKey: boolean}) => void;
  additionalColumns?: React.ReactNode[];
  isHighlighted?: boolean;
}> = ({
  run,
  canTerminateOrDelete,
  onAddTag,
  checked,
  onToggleChecked,
  additionalColumns,
  isHighlighted,
}) => {
  const {pipelineName} = run;
  const repo = useRepositoryForRun(run);

  const isJob = React.useMemo(() => {
    if (repo) {
      const pipelinesAndJobs = repo.match.repository.pipelines;
      const match = pipelinesAndJobs.find((pipelineOrJob) => pipelineOrJob.name === pipelineName);
      return !!match?.isJob;
    }
    return false;
  }, [repo, pipelineName]);

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
      <td>
        {canTerminateOrDelete && onToggleChecked ? (
          <Checkbox checked={!!checked} onChange={onChange} />
        ) : null}
      </td>
      <td>
        <RunStatusTagWithStats status={run.status} runId={run.runId} />
      </td>
      <td>
        <Link to={`/instance/runs/${run.runId}`}>
          <Mono>{titleForRun(run)}</Mono>
        </Link>
      </td>
      <td>
        <Box flex={{direction: 'column', gap: 5}}>
          {isHiddenAssetGroupJob(run.pipelineName) ? (
            <RunAssetKeyTags assetKeys={assetKeysForRun(run)} />
          ) : (
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <PipelineReference
                isJob={isJob}
                showIcon
                pipelineName={run.pipelineName}
                pipelineHrefContext="no-link"
              />
              <Link
                to={
                  repo
                    ? workspacePipelinePath({
                        repoName: repo.match.repository.name,
                        repoLocation: repo.match.repositoryLocation.name,
                        pipelineName: run.pipelineName,
                        isJob,
                      })
                    : workspacePipelinePathGuessRepo(run.pipelineName)
                }
              >
                <Icon name="open_in_new" color={Colors.Blue500} />
              </Link>
            </Box>
          )}
          <RunTags
            tags={run.tags}
            mode={isJob ? (run.mode !== 'default' ? run.mode : null) : run.mode}
            onAddTag={onAddTag}
          />
        </Box>
      </td>
      <td>
        <PipelineSnapshotLink
          snapshotId={run.pipelineSnapshotId || ''}
          pipelineName={run.pipelineName}
          size="normal"
        />
      </td>
      <td>
        <RunTime run={run} />
        <RunStateSummary run={run} />
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
