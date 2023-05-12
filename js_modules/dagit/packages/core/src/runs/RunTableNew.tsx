import {gql} from '@apollo/client';
import {
  Box,
  Checkbox,
  Colors,
  Icon,
  NonIdealState,
  Table,
  Mono,
  Tag,
  Button,
  Dialog,
  DialogBody,
  DialogFooter,
  BaseTag,
  ButtonLink,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {ShortcutHandler} from '../app/ShortcutHandler';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {RunsFilter} from '../graphql/types';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {getPipelineSnapshotLink} from '../pipelines/PipelinePathUtils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {AnchorButton} from '../ui/AnchorButton';
import {useRepositoryForRunWithoutSnapshot} from '../workspace/useRepositoryForRun';
import {workspacePipelinePath, workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

import {AssetKeyTagCollection} from './AssetKeyTagCollection';
import {RunActionsMenu, RunBulkActionsMenu} from './RunActionsMenu';
import {RunCreatedByCell} from './RunCreatedByCell';
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
  belowActionBarComponents?: React.ReactNode;
  hideCreatedBy?: boolean;
}

export const RunTable = (props: RunTableProps) => {
  const {
    runs,
    filter,
    onAddTag,
    highlightedIds,
    actionBarComponents,
    belowActionBarComponents,
    hideCreatedBy,
  } = props;
  const allIds = runs.map((r) => r.id);

  const [{checkedIds}, {onToggleFactory, onToggleAll}] = useSelectionReducer(allIds);

  const canTerminateOrDeleteAny = React.useMemo(() => {
    return runs.some((run) => run.hasTerminatePermission || run.hasDeletePermission);
  }, [runs]);

  function content() {
    if (runs.length === 0) {
      const anyFilter = Object.keys(filter || {}).length;
      return (
        <div>
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
    } else {
      return (
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
              {hideCreatedBy ? null : <th style={{width: 160}}>Created by</th>}
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
      );
    }
  }

  const selectedFragments = runs.filter((run) => checkedIds.has(run.id));

  return (
    <>
      <ActionBar
        top={
          <Box
            flex={{
              direction: 'row',
              justifyContent: 'space-between',
              alignItems: 'center',
              grow: 1,
            }}
          >
            {actionBarComponents}
            <RunBulkActionsMenu
              selected={selectedFragments}
              clearSelection={() => onToggleAll(false)}
            />
          </Box>
        }
        bottom={belowActionBarComponents}
      />
      {content()}
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
  hideCreatedBy?: boolean;
}> = ({
  run,
  canTerminateOrDelete,
  onAddTag,
  checked,
  onToggleChecked,
  additionalColumns,
  isHighlighted,
  hideCreatedBy,
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

  const isReexecution = run.tags.some((tag) => tag.key === DagsterTag.ParentRunId);

  const [showRunTags, setShowRunTags] = React.useState(false);
  const [isHovered, setIsHovered] = React.useState(false);

  return (
    <Row
      highlighted={!!isHighlighted}
      onMouseEnter={() => {
        setIsHovered(true);
      }}
      onMouseLeave={() => {
        setIsHovered(false);
      }}
    >
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
        <Box flex={{direction: 'column', gap: 8}}>
          <RunTime run={run} />
          {isReexecution ? (
            <div>
              <Tag icon="cached">Re-execution</Tag>
            </div>
          ) : null}
        </Box>
      </td>
      <td style={{position: 'relative'}}>
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
          <Box flex={{direction: 'row', gap: 8, wrap: 'wrap'}}>
            {run.tags.length ? (
              <Box>
                <BaseTag
                  fillColor={Colors.Gray100}
                  label={
                    <ButtonLink
                      onClick={() => {
                        setShowRunTags(true);
                      }}
                    >
                      {run.tags.length} tag{run.tags.length === 1 ? '' : 's'}
                    </ButtonLink>
                  }
                />
              </Box>
            ) : null}
            <RunTagsWrapper>
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
            </RunTagsWrapper>
          </Box>
        </Box>
        {isHovered && run.tags.length ? (
          <ShortcutHandler
            key="runtabletags"
            onShortcut={() => {
              setShowRunTags((showRunTags) => !showRunTags);
            }}
            shortcutLabel="t"
            shortcutFilter={(e) => e.code === 'KeyT'}
          >
            {null}
          </ShortcutHandler>
        ) : null}
      </td>
      {hideCreatedBy ? null : (
        <td>
          <RunCreatedByCell run={run} onAddTag={onAddTag} />
        </td>
      )}
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
      <Dialog
        isOpen={showRunTags}
        title="Tags"
        canOutsideClickClose
        canEscapeKeyClose
        onClose={() => {
          setShowRunTags(false);
        }}
      >
        <DialogBody>
          <RunTags
            tags={run.tags}
            mode={isJob ? (run.mode !== 'default' ? run.mode : null) : run.mode}
            onAddTag={onAddTag}
          />
        </DialogBody>
        <DialogFooter topBorder>
          <Button
            intent="primary"
            onClick={() => {
              setShowRunTags(false);
            }}
          >
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </Row>
  );
};

const Row = styled.tr<{highlighted: boolean}>`
  ${({highlighted}) =>
    highlighted ? `box-shadow: inset 3px 3px #bfccd6, inset -3px -3px #bfccd6;` : null}
`;

function ActionBar({top, bottom}: {top: React.ReactNode; bottom?: React.ReactNode}) {
  return (
    <Box flex={{direction: 'column'}} padding={{vertical: 12}}>
      <Box flex={{alignItems: 'center', gap: 12}} padding={{left: 24, right: 24}}>
        {top}
      </Box>
      {bottom ? (
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

const RunTagsWrapper = styled.div`
  display: contents;
  > * {
    display: contents;
  }
`;
