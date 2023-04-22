import {gql} from '@apollo/client';
import {Box, Checkbox, Colors, Icon, NonIdealState, Table, Mono} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {RunsFilter} from '../graphql/types';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';
import {getPipelineSnapshotLink} from '../pipelines/PipelinePathUtils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {AnchorButton} from '../ui/AnchorButton';
import {useRepositoryForRunWithoutSnapshot} from '../workspace/useRepositoryForRun';
import {workspacePipelinePath, workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

import {AssetKeyTagCollection} from './AssetKeyTagCollection';
import {RunActionsMenu, RunBulkActionsMenu} from './RunActionsMenu';
import {RunStatusTagWithStats} from './RunStatusTag';
import {DagsterTag, TagType} from './RunTag';
import {RunTags} from './RunTags';
import {
  assetKeysForRun,
  RunStateSummary,
  RunTime,
  RUN_TIME_FRAGMENT,
  titleForRun,
} from './RunUtils';
import {RunFilterToken} from './RunsFilterInput';
import {RunTableRunFragment} from './types/RunTable.types';

interface RunTableProps {
  runs: RunTableRunFragment[];
  filter?: RunsFilter;
  onAddTag?: (token: RunFilterToken) => void;
  actionBarComponents?: React.ReactNode;
  highlightedIds?: string[];
  additionalColumnHeaders?: React.ReactNode[];
  additionalColumnsForRow?: (run: RunTableRunFragment) => React.ReactNode[];
  belowActionBarComponents?: React.ReactNode[];
}

export const RunTable = (props: RunTableProps) => {
  const {
    runs,
    filter,
    onAddTag,
    highlightedIds,
    actionBarComponents,
    belowActionBarComponents,
  } = props;
  const allIds = runs.map((r) => r.id);

  const [{checkedIds}, {onToggleFactory, onToggleAll}] = useSelectionReducer(allIds);

  const canTerminateOrDeleteAny = React.useMemo(() => {
    return runs.some((run) => run.hasTerminatePermission || run.hasDeletePermission);
  }, [runs]);

  if (runs.length === 0) {
    const anyFilter = Object.keys(filter || {}).length;
    return (
      <div>
        <Box border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}>
          {actionBarComponents ? (
            <ActionBar top={actionBarComponents} bottom={belowActionBarComponents} />
          ) : null}
        </Box>
        <Box margin={{vertical: 32}}>
          {anyFilter ? (
            <NonIdealState
              icon="run"
              title="No matching runs"
              description="No runs were found for this filter."
            />
          ) : (
            <NonIdealState
              icon="run"
              title="No runs found"
              description={
                <Box flex={{direction: 'column', gap: 12}}>
                  <div>You have not launched any runs yet.</div>
                  <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
                    <AnchorButton icon={<Icon name="add_circle" />} to="/overview/jobs">
                      Launch a run
                    </AnchorButton>
                    <span>or</span>
                    <AnchorButton icon={<Icon name="materialization" />} to="/asset-groups">
                      Materialize an asset
                    </AnchorButton>
                  </Box>
                </Box>
              }
            />
          )}
        </Box>
      </div>
    );
  }

  const selectedFragments = runs.filter((run) => checkedIds.has(run.id));

  return (
    <>
      <ActionBar
        top={
          <>
            {actionBarComponents}
            <div style={{flex: 1}} />
            <RunBulkActionsMenu
              selected={selectedFragments}
              clearSelection={() => onToggleAll(false)}
            />
          </>
        }
        bottom={belowActionBarComponents}
      />
      <Table>
        <thead>
          <tr>
            <th style={{width: 42, paddingTop: 0, paddingBottom: 0}}>
              {canTerminateOrDeleteAny ? (
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
            <th style={{width: 90}}>Run ID</th>
            <th style={{width: 180}}>Created date</th>
            <th>Target</th>
            <th style={{width: 160}}>Created by</th>
            <th style={{width: 120}}>Status</th>
            <th style={{width: 190}}>Duration</th>
            {props.additionalColumnHeaders}
            <th style={{width: 52}} />
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <RunRow
              canTerminateOrDelete={run.hasTerminatePermission || run.hasDeletePermission}
              run={run}
              key={run.id}
              onAddTag={onAddTag}
              checked={checkedIds.has(run.id)}
              additionalColumns={props.additionalColumnsForRow?.(run)}
              onToggleChecked={onToggleFactory(run.id)}
              isHighlighted={highlightedIds && highlightedIds.includes(run.id)}
            />
          ))}
        </tbody>
      </Table>
    </>
  );
};

export const RUN_TABLE_RUN_FRAGMENT = gql`
  fragment RunTableRunNewFragment on Run {
    id
    status
    stepKeysToExecute
    canTerminate
    hasReExecutePermission
    hasTerminatePermission
    hasDeletePermission
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
  const repo = useRepositoryForRunWithoutSnapshot(run);

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

  const {RunCreatedByCell} = useLaunchPadHooks();

  return (
    <Row highlighted={!!isHighlighted}>
      <td>
        {canTerminateOrDelete && onToggleChecked ? (
          <Checkbox checked={!!checked} onChange={onChange} />
        ) : null}
      </td>
      <td>
        <Link to={`/runs/${run.id}`}>
          <Mono>{titleForRun(run)}</Mono>
        </Link>
      </td>
      <td>
        <RunTime run={run} />
      </td>
      <td>
        <Box flex={{direction: 'column', gap: 5}}>
          {isHiddenAssetGroupJob(run.pipelineName) ? (
            <AssetKeyTagCollection assetKeys={assetKeysForRun(run)} />
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
                target="_blank"
              >
                <Icon name="open_in_new" color={Colors.Blue500} />
              </Link>
            </Box>
          )}
          <RunTags
            tags={
              [
                run.pipelineSnapshotId
                  ? {
                      key: DagsterTag.SnapshotID,
                      value: run.pipelineSnapshotId?.slice(0, 8) || '',
                      link: run.pipelineSnapshotId
                        ? getPipelineSnapshotLink(run.pipelineName, run.pipelineSnapshotId)
                        : undefined,
                    }
                  : null,
                run.tags.find((tag) => tag.key === DagsterTag.Partition),
              ].filter((x) => x) as TagType[]
            }
            mode={isJob ? (run.mode !== 'default' ? run.mode : null) : run.mode}
            onAddTag={onAddTag}
          />
        </Box>
      </td>
      <td>
        <RunCreatedByCell run={run} />
      </td>
      <td>
        <RunStatusTagWithStats status={run.status} runId={run.id} />
      </td>
      <td>
        <RunStateSummary run={run} />
      </td>
      {additionalColumns}
      <td>
        <RunActionsMenu run={run} onAddTag={onAddTag} />
      </td>
    </Row>
  );
};

const Row = styled.tr<{highlighted: boolean}>`
  ${({highlighted}) =>
    highlighted ? `box-shadow: inset 3px 3px #bfccd6, inset -3px -3px #bfccd6;` : null}
`;

function ActionBar({top, bottom}: {top: React.ReactNode; bottom?: React.ReactNode[]}) {
  return (
    <Box flex={{direction: 'column'}} padding={{vertical: 12}}>
      <Box flex={{alignItems: 'center', gap: 12}} padding={{left: 24, right: 24}}>
        {top}
      </Box>
      {bottom && bottom.length > 0 ? (
        <Box
          margin={{top: 12}}
          padding={{left: 24, right: 12, top: 8}}
          border={{side: 'top', width: 1, color: Colors.KeylineGray}}
          flex={{gap: 8}}
        >
          {bottom}
        </Box>
      ) : null}
    </Box>
  );
}
