import {
  Box,
  Button,
  ButtonLink,
  Caption,
  Checkbox,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Mono,
  Tag,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {ShortcutHandler} from '../app/ShortcutHandler';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {PipelineTag} from '../graphql/types';
import {PipelineReference} from '../pipelines/PipelineReference';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';
import {useRepositoryForRunWithoutSnapshot} from '../workspace/useRepositoryForRun';

import {AssetCheckTagCollection, AssetKeyTagCollection} from './AssetTagCollections';
import {CreatedByTagCell} from './CreatedByTag';
import {RunActionsMenu} from './RunActionsMenu';
import {RunStatusTagWithStats} from './RunStatusTag';
import {DagsterTag, TagType} from './RunTag';
import {RunTags} from './RunTags';
import {RunStateSummary, RunTime, assetKeysForRun, titleForRun} from './RunUtils';
import {RunFilterToken, runsPathWithFilters} from './RunsFilterInput';
import {RunTableRunFragment} from './types/RunTable.types';
import {useTagPinning} from './useTagPinning';

export const RunRow = ({
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
  const {isTagPinned, onToggleTagPin} = useTagPinning();

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

  const allTagsWithPinned = React.useMemo(() => {
    const allTags: Omit<PipelineTag, '__typename'>[] = [...run.tags];
    if ((isJob && run.mode !== 'default') || !isJob) {
      allTags.push({key: 'mode', value: run.mode});
    }
    return allTags.map((tag) => {
      return {...tag, pinned: isTagPinned(tag)};
    });
  }, [run, isJob, isTagPinned]);

  const isReexecution = run.tags.some((tag) => tag.key === DagsterTag.ParentRunId);

  const [showRunTags, setShowRunTags] = React.useState(false);
  const [isHovered, setIsHovered] = React.useState(false);

  const tagsToShow = React.useMemo(() => {
    const targetBackfill = allTagsWithPinned.find((tag) => tag.key === DagsterTag.Backfill);
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
  }, [allTagsWithPinned, run.assetSelection?.length]);

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
          <RunTargetLink isJob={isJob} run={run} repoAddress={repoAddressGuess} />
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
                  color={Colors.Gray700}
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

const RunTagsWrapper = styled.div`
  display: contents;
  > * {
    display: contents;
  }
`;

const RunTargetLink = ({
  run,
  isJob,
  repoAddress,
}: {
  isJob: boolean;
  run: RunTableRunFragment;
  repoAddress: RepoAddress | null;
}) => {
  return isHiddenAssetGroupJob(run.pipelineName) ? (
    <Box flex={{gap: 16, alignItems: 'end', wrap: 'wrap'}}>
      <AssetKeyTagCollection assetKeys={assetKeysForRun(run)} />
      <AssetCheckTagCollection assetChecks={run.assetCheckSelection} />
    </Box>
  ) : (
    <PipelineReference
      isJob={isJob}
      showIcon
      pipelineName={run.pipelineName}
      pipelineHrefContext={repoAddress || 'repo-unknown'}
    />
  );
};
