import {
  Box,
  ButtonLink,
  Caption,
  Checkbox,
  Colors,
  Icon,
  Mono,
  Tag,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {CreatedByTagCell} from './CreatedByTag';
import {QueuedRunCriteriaDialog} from './QueuedRunCriteriaDialog';
import {RunActionsMenu} from './RunActionsMenu';
import {RunRowTags} from './RunRowTags';
import {RunStatusTag, RunStatusTagWithStats} from './RunStatusTag';
import {DagsterTag} from './RunTag';
import {RunTags} from './RunTags';
import {RunTargetLink} from './RunTargetLink';
import {RunStateSummary, RunTime, titleForRun} from './RunUtils';
import {getBackfillPath} from './RunsFeedUtils';
import {RunFilterToken} from './RunsFilterInput';
import {RunTimeFragment} from './types/RunUtils.types';
import {RunsFeedTableEntryFragment} from './types/RunsFeedTableEntryFragment.types';
import {RunStatus} from '../graphql/types';
import {BackfillActionsMenu} from '../instance/backfill/BackfillActionsMenu';
import {BackfillTarget} from '../instance/backfill/BackfillRow';
import {HeaderCell, HeaderRow, RowCell} from '../ui/VirtualizedTable';
import {appendCurrentQueryParams} from '../util/appendCurrentQueryParams';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

export const RunsFeedRow = ({
  entry,
  onAddTag,
  onShowPartitions,
  checked,
  onToggleChecked,
  refetch,
  hideTags,
}: {
  entry: RunsFeedTableEntryFragment;
  refetch: () => void;
  onShowPartitions: () => void;
  onAddTag?: (token: RunFilterToken) => void;
  checked?: boolean;
  onToggleChecked?: (values: {checked: boolean; shiftKey: boolean}) => void;
  additionalColumns?: React.ReactNode[];
  hideCreatedBy?: boolean;
  hideTags?: string[];
}) => {
  const onChange = (e: React.FormEvent<HTMLInputElement>) => {
    if (e.target instanceof HTMLInputElement) {
      const {checked} = e.target;
      const shiftKey =
        e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
      if (onToggleChecked) {
        onToggleChecked({checked, shiftKey});
      }
    }
  };

  const isReexecution = entry.tags.some((tag) => tag.key === DagsterTag.ParentRunId);
  const repoAddress = React.useMemo(
    () =>
      entry.__typename === 'Run' && entry.repositoryOrigin
        ? buildRepoAddress(
            entry.repositoryOrigin.repositoryName,
            entry.repositoryOrigin.repositoryLocationName,
          )
        : null,
    [entry],
  );

  const [showQueueCriteria, setShowQueueCriteria] = React.useState(false);
  const [isHovered, setIsHovered] = React.useState(false);

  const runTime: RunTimeFragment = {
    id: entry.id,
    creationTime: entry.creationTime,
    startTime: entry.startTime,
    endTime: entry.endTime,
    updateTime: entry.creationTime,
    status: entry.runStatus,
    __typename: 'Run',
  };

  const partitionTag =
    entry.__typename === 'Run' ? entry.tags.find((t) => t.key === DagsterTag.Partition) : null;

  return (
    <RowGrid
      border="bottom"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <RowCell>
        <Checkbox checked={!!checked} onChange={onChange} />
      </RowCell>

      <RowCell>
        <Box flex={{direction: 'column', gap: 5}}>
          <Link
            to={
              entry.__typename === 'PartitionBackfill'
                ? appendCurrentQueryParams(getBackfillPath(entry.id, entry.isAssetBackfill))
                : `/runs/${entry.id}`
            }
          >
            <Box flex={{gap: 4, alignItems: 'center'}}>
              <Icon name={entry.__typename === 'PartitionBackfill' ? 'run_with_subruns' : 'run'} />
              <Mono>{titleForRun(entry)}</Mono>
            </Box>
          </Link>
          <Box
            flex={{direction: 'row', alignItems: 'center', wrap: 'wrap'}}
            style={{gap: '4px 8px', lineHeight: 0}}
          >
            {entry.__typename === 'PartitionBackfill' ? (
              <Tag intent="none">Backfill</Tag>
            ) : undefined}

            <RunRowTags
              run={{...entry, mode: 'default'}}
              isJob={true}
              isHovered={isHovered}
              onAddTag={onAddTag}
              hideTags={hideTags}
              hidePartition
            />

            {entry.runStatus === RunStatus.QUEUED ? (
              <Caption>
                <ButtonLink
                  onClick={() => {
                    setShowQueueCriteria(true);
                  }}
                  color={Colors.textLight()}
                >
                  View queue criteria
                </ButtonLink>
              </Caption>
            ) : null}
          </Box>
        </Box>
      </RowCell>
      <RowCell style={{flexDirection: 'row', alignItems: 'flex-start'}}>
        {entry.__typename === 'Run' ? (
          <RunTargetLink
            isJob={true}
            run={{...entry, pipelineName: entry.jobName!, stepKeysToExecute: []}}
            repoAddress={repoAddress}
            useTags={true}
            extraTags={
              partitionTag
                ? [<RunTags key="partition" tags={[partitionTag]} onAddTag={onAddTag} />]
                : []
            }
          />
        ) : (
          <BackfillTarget
            backfill={entry}
            repoAddress={null}
            useTags={true}
            onShowPartitions={onShowPartitions}
          />
        )}
      </RowCell>
      <RowCell>
        <CreatedByTagCell tags={entry.tags || []} onAddTag={onAddTag} repoAddress={repoAddress} />
      </RowCell>
      <RowCell>
        <div>
          {entry.__typename === 'PartitionBackfill' ? (
            <RunStatusTag status={entry.runStatus} />
          ) : (
            <RunStatusTagWithStats status={entry.runStatus} runId={entry.id} />
          )}
        </div>
      </RowCell>
      <RowCell style={{flexDirection: 'column', gap: 4}}>
        <RunTime run={runTime} />
        {isReexecution ? (
          <div>
            <Tag icon="cached">Re-execution</Tag>
          </div>
        ) : null}
      </RowCell>
      <RowCell>
        <RunStateSummary run={runTime} />
      </RowCell>
      <RowCell>
        {entry.__typename === 'PartitionBackfill' ? (
          <BackfillActionsMenu
            backfill={{...entry, status: entry.backfillStatus}}
            refetch={refetch}
            anchorLabel="View"
          />
        ) : (
          <RunActionsMenu run={entry} onAddTag={onAddTag} anchorLabel="View" />
        )}
      </RowCell>
      <QueuedRunCriteriaDialog
        run={entry}
        isOpen={showQueueCriteria}
        onClose={() => setShowQueueCriteria(false)}
      />
    </RowGrid>
  );
};

const TEMPLATE_COLUMNS =
  '60px minmax(0, 1.5fr) minmax(0, 1.2fr) minmax(0, 1fr) 140px 170px 120px 132px';

export const RunsFeedTableHeader = ({checkbox}: {checkbox: React.ReactNode}) => {
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>
        <div style={{position: 'relative', top: '-1px'}}>{checkbox}</div>
      </HeaderCell>
      <HeaderCell>ID</HeaderCell>
      <HeaderCell>Target</HeaderCell>
      <HeaderCell>Launched by</HeaderCell>
      <HeaderCell>Status</HeaderCell>
      <HeaderCell>Created at</HeaderCell>
      <HeaderCell>Duration</HeaderCell>
      <HeaderCell></HeaderCell>
    </HeaderRow>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
`;
