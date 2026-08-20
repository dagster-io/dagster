import {
  Box,
  ButtonLink,
  Checkbox,
  Colors,
  HeaderCell,
  HeaderRow,
  Icon,
  RowCell,
  Tag,
  Text,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {CreatedByTagCell} from './CreatedByTag';
import {RunActionsMenu} from './RunActionsMenu';
import {RunRowTags} from './RunRowTags';
import {RunStatusTag, RunStatusTagWithStats} from './RunStatusTag';
import {DagsterTag} from './RunTag';
import {RunTags} from './RunTags';
import {RunTargetLink} from './RunTargetLink';
import {RunStateSummary, RunTime, titleForRun} from './RunUtils';
import {ColumnResizeHandle, RunsFeedColumnKey, useRunsFeedColumns} from './RunsFeedColumns';
import {RunsFeedDialogState} from './RunsFeedTable';
import {getBackfillPath} from './RunsFeedUtils';
import {RunFilterToken} from './RunsFilterInput';
import styles from './css/RunsFeedRow.module.css';
import {RunTimeFragment} from './types/RunUtils.types';
import {RunsFeedTableEntryFragment} from './types/RunsFeedTableEntryFragment.types';
import {RunStatus} from '../graphql/types';
import {BackfillActionsMenu} from '../instance/backfill/BackfillActionsMenu';
import {BackfillTarget} from '../instance/backfill/BackfillRow';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

export const RunsFeedRow = ({
  entry,
  onAddTag,
  onShowDialog,
  checked,
  onToggleChecked,
  refetch,
  hideTags,
}: {
  entry: RunsFeedTableEntryFragment;
  refetch: () => void;
  onShowDialog: (dialog: RunsFeedDialogState) => void;
  onAddTag?: (token: RunFilterToken) => void;
  checked?: boolean;
  onToggleChecked?: (values: {checked: boolean; shiftKey: boolean}) => void;
  additionalColumns?: React.ReactNode[];
  hideCreatedBy?: boolean;
  hideTags?: string[];
}) => {
  const {visibleColumns, templateColumns, minWidth} = useRunsFeedColumns();

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

  const cells: Record<RunsFeedColumnKey, React.ReactNode> = {
    id: (
      <RowCell>
        <Box flex={{direction: 'column', gap: 5}}>
          <Link
            to={
              entry.__typename === 'PartitionBackfill'
                ? getBackfillPath(entry.id)
                : `/runs/${entry.id}`
            }
          >
            <Box flex={{gap: 4, alignItems: 'center'}}>
              <Icon name={entry.__typename === 'PartitionBackfill' ? 'run_with_subruns' : 'run'} />
              <Text size={14} family="mono">
                {titleForRun(entry)}
              </Text>
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
              isHovered={isHovered}
              onAddTag={onAddTag}
              hideTags={hideTags}
            />

            {entry.runStatus === RunStatus.QUEUED ? (
              <Text size={12}>
                <ButtonLink
                  onClick={() => onShowDialog({type: 'queue-criteria', entry})}
                  color={Colors.textLight()}
                >
                  View queue criteria
                </ButtonLink>
              </Text>
            ) : null}
          </Box>
        </Box>
      </RowCell>
    ),
    target: (
      <RowCell style={{flexDirection: 'row', alignItems: 'flex-start'}}>
        {entry.__typename === 'Run' ? (
          <RunTargetLink
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            run={{...entry, pipelineName: entry.jobName!}}
            repoAddress={repoAddress}
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
            onShowPartitions={() => onShowDialog({type: 'partitions', backfillId: entry.id})}
          />
        )}
      </RowCell>
    ),
    launchedBy: (
      <RowCell>
        <CreatedByTagCell tags={entry.tags || []} onAddTag={onAddTag} repoAddress={repoAddress} />
      </RowCell>
    ),
    status: (
      <RowCell>
        <div>
          {entry.__typename === 'PartitionBackfill' ? (
            <RunStatusTag status={entry.runStatus} />
          ) : (
            <RunStatusTagWithStats status={entry.runStatus} runId={entry.id} />
          )}
        </div>
      </RowCell>
    ),
    createdAt: (
      <RowCell style={{flexDirection: 'column', gap: 4}}>
        <RunTime run={runTime} />
        {isReexecution ? (
          <div>
            <Tag icon="cached">Re-execution</Tag>
          </div>
        ) : null}
      </RowCell>
    ),
    duration: (
      <RowCell>
        <RunStateSummary run={runTime} />
      </RowCell>
    ),
  };

  return (
    <Box
      className={styles.rowGrid}
      style={{gridTemplateColumns: templateColumns, minWidth}}
      border="bottom"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <RowCell>
        <Checkbox checked={!!checked} onChange={onChange} />
      </RowCell>

      {visibleColumns.map((column) => (
        <React.Fragment key={column.key}>{cells[column.key]}</React.Fragment>
      ))}

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
    </Box>
  );
};

export const RunsFeedTableHeader = ({checkbox}: {checkbox: React.ReactNode}) => {
  const {visibleColumns, templateColumns, minWidth} = useRunsFeedColumns();

  return (
    <HeaderRow templateColumns={templateColumns} minWidth={minWidth} sticky>
      <HeaderCell>
        <div style={{position: 'relative', top: '-1px'}}>{checkbox}</div>
      </HeaderCell>
      {visibleColumns.map((column) => (
        <HeaderCell key={column.key} style={{position: 'relative'}}>
          {column.label}
          <ColumnResizeHandle columnKey={column.key} />
        </HeaderCell>
      ))}
      <HeaderCell></HeaderCell>
    </HeaderRow>
  );
};
