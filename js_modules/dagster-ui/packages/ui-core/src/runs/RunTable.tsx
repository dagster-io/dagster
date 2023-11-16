import {gql} from '@apollo/client';
import {
  Box,
  Checkbox,
  Icon,
  NonIdealState,
  Table,
  Mono,
  Tag,
  Button,
  Dialog,
  DialogBody,
  DialogFooter,
  ButtonLink,
  ProductTour,
  ProductTourPosition,
  Caption,
  colorTextLighter,
  colorLinkDefault,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {ShortcutHandler} from '../app/ShortcutHandler';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {RunsFilter} from '../graphql/types';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {PipelineReference} from '../pipelines/PipelineReference';
import {AnchorButton} from '../ui/AnchorButton';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {useRepositoryForRunWithoutSnapshot} from '../workspace/useRepositoryForRun';
import {workspacePipelinePath, workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

import {AssetKeyTagCollection, AssetCheckTagCollection} from './AssetTagCollections';
import {CreatedByTagCell} from './CreatedByTag';
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
import {RunFilterToken, runsPathWithFilters} from './RunsFilterInput';
import ShowAndHideTagsMP4 from './ShowAndHideRunTags.mp4';
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
  additionalActionsForRun?: (run: RunTableRunFragment) => JSX.Element[];
  emptyState?: () => React.ReactNode;
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
    emptyState,
  } = props;
  const allIds = runs.map((r) => r.id);

  const [{checkedIds}, {onToggleFactory, onToggleAll}] = useSelectionReducer(allIds);

  const canTerminateOrDeleteAny = React.useMemo(() => {
    return runs.some((run) => run.hasTerminatePermission || run.hasDeletePermission);
  }, [runs]);

  function content() {
    if (runs.length === 0) {
      const anyFilter = !!Object.keys(filter || {}).length;
      if (emptyState) {
        return <>{emptyState()}</>;
      }

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
              {canTerminateOrDeleteAny ? (
                <th style={{width: 42, paddingTop: 0, paddingBottom: 0}}>
                  <Checkbox
                    indeterminate={checkedIds.size > 0 && checkedIds.size !== runs.length}
                    checked={checkedIds.size === runs.length}
                    onChange={(e: React.FormEvent<HTMLInputElement>) => {
                      if (e.target instanceof HTMLInputElement) {
                        onToggleAll(e.target.checked);
                      }
                    }}
                  />
                </th>
              ) : null}
              <th style={{width: 90}}>Run ID</th>
              <th style={{width: 180}}>Created date</th>
              <th>
                <TargetHeader />
              </th>
              {hideCreatedBy ? null : <th style={{width: 160}}>Launched by</th>}
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
                additionalActionsForRun={props.additionalActionsForRun}
                onToggleChecked={onToggleFactory(run.id)}
                isHighlighted={highlightedIds && highlightedIds.includes(run.id)}
                hideCreatedBy={hideCreatedBy}
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

export const RUN_TAGS_FRAGMENT = gql`
  fragment RunTagsFragment on PipelineTag {
    key
    value
  }
`;

export const RUN_TABLE_RUN_FRAGMENT = gql`
  fragment RunTableRunFragment on Run {
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
    assetCheckSelection {
      name
      assetKey {
        path
      }
    }
    status
    tags {
      ...RunTagsFragment
    }
    ...RunTimeFragment
  }

  ${RUN_TIME_FRAGMENT}
  ${RUN_TAGS_FRAGMENT}
`;

const RunRow = ({
  run,
  canTerminateOrDelete,
  onAddTag,
  checked,
  onToggleChecked,
  additionalColumns,
  additionalActionsForRun,
  isHighlighted,
  hideCreatedBy,
}: {
  run: RunTableRunFragment;
  canTerminateOrDelete: boolean;
  onAddTag?: (token: RunFilterToken) => void;
  checked?: boolean;
  onToggleChecked?: (values: {checked: boolean; shiftKey: boolean}) => void;
  additionalColumns?: React.ReactNode[];
  additionalActionsForRun?: (run: RunTableRunFragment) => React.ReactNode[];
  isHighlighted?: boolean;
  hideCreatedBy?: boolean;
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

  const repoAddressGuess = React.useMemo(() => {
    if (repo) {
      const {match} = repo;
      return buildRepoAddress(match.repository.name, match.repositoryLocation.name);
    }
    return null;
  }, [repo]);

  const onChange = (e: React.FormEvent<HTMLInputElement>) => {
    if (e.target instanceof HTMLInputElement) {
      const {checked} = e.target;
      const shiftKey =
        e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
      onToggleChecked && onToggleChecked({checked, shiftKey});
    }
  };

  // Most system tags are unpinned by default so we track pinned for these.
  const [pinnedSystemTags, setPinnedSystemTags] = useStateWithStorage(
    'pinned-system-tags',
    (value) => {
      if (Array.isArray(value)) {
        return value;
      }
      return [];
    },
  );

  // All user tags are pinned by default so we track unpinned.
  const [unpinnedTags, setUnpinnedTags] = useStateWithStorage('unpinned-tags', (value) => {
    if (Array.isArray(value)) {
      return value;
    }
    return [];
  });

  const allTagsWithPinned = React.useMemo(() => {
    const allTags: Omit<(typeof run.tags)[0], '__typename'>[] = [...run.tags];
    if ((isJob && run.mode !== 'default') || !isJob) {
      allTags.push({
        key: 'mode',
        value: run.mode,
      });
    }
    return allTags.map((tag) => {
      return {
        ...tag,
        pinned: isUnpinnedByDefaultSystemTag(tag.key)
          ? pinnedSystemTags.indexOf(tag.key) !== -1
          : unpinnedTags.indexOf(tag.key) === -1,
      };
    });
  }, [run, isJob, pinnedSystemTags, unpinnedTags]);

  const isReexecution = run.tags.some((tag) => tag.key === DagsterTag.ParentRunId);

  const targetBackfill = allTagsWithPinned.find((tag) => tag.key === DagsterTag.Backfill);

  const [showRunTags, setShowRunTags] = React.useState(false);
  const [isHovered, setIsHovered] = React.useState(false);

  const tagsToShow = React.useMemo(() => {
    const tagKeys: Set<string> = new Set([]);
    const tags: TagType[] = [];
    if (targetBackfill && targetBackfill.pinned) {
      const link = run.assetSelection?.length
        ? `/overview/backfills/${targetBackfill.value}`
        : runsPathWithFilters([
            {
              token: 'tag',
              value: `${DagsterTag.Backfill}=${targetBackfill.value}`,
            },
          ]);
      tags.push({
        ...targetBackfill,
        link,
      });
      tagKeys.add(DagsterTag.Backfill as string);
    }
    allTagsWithPinned.forEach((tag) => {
      if (tagKeys.has(tag.key)) {
        // We already added this tag
        return;
      }
      if (tag.pinned) {
        tags.push(tag);
      }
    });
    return tags;
  }, [targetBackfill, allTagsWithPinned, run.assetSelection?.length]);

  const onToggleTagPin = React.useCallback(
    (tagKey: string) => {
      if (isUnpinnedByDefaultSystemTag(tagKey)) {
        setPinnedSystemTags((pinnedSystemTags) => toggleTag(pinnedSystemTags, tagKey));
      } else {
        setUnpinnedTags((unpinnedTags) => toggleTag(unpinnedTags, tagKey));
      }
    },
    [setUnpinnedTags, setPinnedSystemTags],
  );

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
      {canTerminateOrDelete ? (
        <td>{onToggleChecked ? <Checkbox checked={!!checked} onChange={onChange} /> : null}</td>
      ) : null}
      <td>
        <Link to={`/runs/${run.id}`}>
          <Mono>{titleForRun(run)}</Mono>
        </Link>
      </td>
      <td>
        <Box flex={{direction: 'column', gap: 4}}>
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
            <Box flex={{gap: 16}}>
              <AssetKeyTagCollection assetKeys={assetKeysForRun(run)} />
              <AssetCheckTagCollection assetChecks={run.assetCheckSelection} />
            </Box>
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
                <Icon name="open_in_new" color={colorLinkDefault()} />
              </Link>
            </Box>
          )}
          <Box
            flex={{direction: 'row', alignItems: 'center', wrap: 'wrap'}}
            style={{gap: '4px 8px'}}
          >
            <RunTagsWrapper>
              {tagsToShow.length ? (
                <RunTags tags={tagsToShow} onAddTag={onAddTag} onToggleTagPin={onToggleTagPin} />
              ) : null}
            </RunTagsWrapper>
            {allTagsWithPinned.length > tagsToShow.length ? (
              <Caption>
                <ButtonLink
                  onClick={() => {
                    setShowRunTags(true);
                  }}
                  color={colorTextLighter()}
                  style={{margin: '-4px', padding: '4px'}}
                >
                  View all tags ({allTagsWithPinned.length})
                </ButtonLink>
              </Caption>
            ) : null}
          </Box>
        </Box>
        {isHovered && allTagsWithPinned.length ? (
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
          <CreatedByTagCell
            repoAddress={repoAddressGuess}
            tags={run.tags || []}
            onAddTag={onAddTag}
          />
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
        <RunActionsMenu
          run={run}
          onAddTag={onAddTag}
          additionalActionsForRun={additionalActionsForRun}
        />
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
          <RunTags tags={allTagsWithPinned} onAddTag={onAddTag} onToggleTagPin={onToggleTagPin} />
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
      <Box flex={{alignItems: 'center', gap: 12}} padding={{left: 24, right: 12}}>
        {top}
      </Box>
      {bottom ? (
        <Box
          margin={{top: 12}}
          padding={{left: 24, right: 12, top: 8}}
          border="top"
          flex={{gap: 8, wrap: 'wrap'}}
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

function isUnpinnedByDefaultSystemTag(key: string) {
  return (
    (key.startsWith(DagsterTag.Namespace) &&
      key !== DagsterTag.Partition &&
      key !== DagsterTag.Backfill) ||
    key === 'mode'
  );
}

function toggleTag(tagsArr: string[] | undefined, tagKey: string): string[] {
  const tags = tagsArr || [];
  if (tags.indexOf(tagKey) !== -1) {
    return tags.filter((key) => key !== tagKey);
  } else {
    return [...tags, tagKey];
  }
}

function TargetHeader() {
  const [hideTabPinningNux, setHideTabPinningNux] = useStateWithStorage<any>(
    'RunTableTabPinningNux',
    (value) => value,
  );
  if (hideTabPinningNux) {
    return <div>Target</div>;
  }
  return (
    <ProductTour
      title="Hide and show run tags"
      description={
        <>
          You can show tags that you prefer quick access to and hide tags you don&apos;t by hovering
          over the tag and selecting the show/hide tag option.
        </>
      }
      position={ProductTourPosition.BOTTOM_RIGHT}
      video={ShowAndHideTagsMP4}
      width="616px"
      actions={{
        dismiss: () => {
          setHideTabPinningNux('1');
        },
      }}
    >
      <div>Target</div>
    </ProductTour>
  );
}
