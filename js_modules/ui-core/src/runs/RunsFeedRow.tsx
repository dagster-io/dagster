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
import {Link, useHistory} from 'react-router-dom';

import {CreatedByTagCell} from './CreatedByTag';
import {RunActionsMenu} from './RunActionsMenu';
import {RunRowTags} from './RunRowTags';
import {RunStatusTag, RunStatusTagWithStats} from './RunStatusTag';
import {DagsterTag} from './RunTag';
import {RunTags} from './RunTags';
import {RunTargetLink} from './RunTargetLink';
import {RunStateSummary, RunTime, titleForRun} from './RunUtils';
import {RunsFeedDialogState} from './RunsFeedTable';
import {getBackfillPath} from './RunsFeedUtils';
import {RunFilterToken} from './RunsFilterInput';
import styles from './css/RunsFeedRow.module.css';
import {RunTimeFragment} from './types/RunUtils.types';
import {RunsFeedTableEntryFragment} from './types/RunsFeedTableEntryFragment.types';
import {LayoutContext} from '../app/LayoutProvider';
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
  const history = useHistory();

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

  // A phone row answers "what ran, did it work, when, how long". Bulk selection,
  // the launcher, tag chips and the "View" button are desktop concerns: dropping
  // them makes the row two dense lines, so a screenful is nine runs instead of
  // three. Tags and config stay reachable from the actions menu.
  const {isMobileScreen} = React.useContext(LayoutContext).nav;

  const runPath =
    entry.__typename === 'PartitionBackfill' ? getBackfillPath(entry.id) : `/runs/${entry.id}`;

  if (isMobileScreen) {
    // The row itself opens the run; taps on inner links/buttons keep their own behaviour.
    const onRowClick = (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target instanceof Element && e.target.closest('a, button, input, [role="button"]')) {
        return;
      }
      history.push(runPath);
    };

    return (
      <Box className={styles.mobileRow} border="bottom" onClick={onRowClick}>
        <div className={styles.mobileStatus}>
          {entry.__typename === 'PartitionBackfill' ? (
            <RunStatusTag status={entry.runStatus} />
          ) : (
            <RunStatusTagWithStats status={entry.runStatus} runId={entry.id} />
          )}
        </div>
        <div className={styles.mobileTarget}>
          {entry.__typename === 'Run' ? (
            <RunTargetLink
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              run={{...entry, pipelineName: entry.jobName!}}
              repoAddress={repoAddress}
              extraTags={[]}
            />
          ) : (
            <BackfillTarget
              backfill={entry}
              repoAddress={null}
              useTags={true}
              onShowPartitions={() => onShowDialog({type: 'partitions', backfillId: entry.id})}
            />
          )}
        </div>
        <div className={styles.mobileMeta}>
          <Link to={runPath} className={styles.mobileId}>
            <Icon
              name={entry.__typename === 'PartitionBackfill' ? 'run_with_subruns' : 'run'}
              size={16}
            />
            <Text size={12} family="mono">
              {titleForRun(entry)}
            </Text>
          </Link>
          <span className={styles.mobileMetaItem}>
            <RunStateSummary run={runTime} />
          </span>
          <span className={styles.mobileMetaItem}>
            <RunTime run={runTime} />
          </span>
          {isReexecution ? <Icon name="cached" size={16} /> : null}
        </div>
        <div className={styles.mobileMenu}>
          {entry.__typename === 'PartitionBackfill' ? (
            <BackfillActionsMenu
              backfill={{...entry, status: entry.backfillStatus}}
              refetch={refetch}
            />
          ) : (
            <RunActionsMenu run={entry} onAddTag={onAddTag} iconOnly />
          )}
        </div>
      </Box>
    );
  }

  return (
    <Box
      className={styles.rowGrid}
      border="bottom"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <RowCell className={styles.cellCheckbox}>
        <Checkbox checked={!!checked} onChange={onChange} />
      </RowCell>

      <RowCell className={styles.cellId}>
        <Box flex={{direction: 'column', gap: 5}}>
          <Link to={runPath}>
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
      <RowCell
        className={styles.cellTarget}
        style={{flexDirection: 'row', alignItems: 'flex-start'}}
      >
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
      <RowCell className={styles.cellCreatedBy}>
        <CreatedByTagCell tags={entry.tags || []} onAddTag={onAddTag} repoAddress={repoAddress} />
      </RowCell>
      <RowCell className={styles.cellStatus}>
        <div>
          {entry.__typename === 'PartitionBackfill' ? (
            <RunStatusTag status={entry.runStatus} />
          ) : (
            <RunStatusTagWithStats status={entry.runStatus} runId={entry.id} />
          )}
        </div>
      </RowCell>
      <RowCell className={styles.cellTime} style={{flexDirection: 'column', gap: 4}}>
        <RunTime run={runTime} />
        {isReexecution ? (
          <div>
            <Tag icon="cached">Re-execution</Tag>
          </div>
        ) : null}
      </RowCell>
      <RowCell className={styles.cellDuration}>
        <RunStateSummary run={runTime} />
      </RowCell>
      <RowCell className={styles.cellMenu}>
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

const TEMPLATE_COLUMNS =
  '60px minmax(0, 1.5fr) minmax(0, 1.2fr) minmax(0, 1fr) 140px 170px 120px 132px';

export const RunsFeedTableHeader = ({checkbox}: {checkbox: React.ReactNode}) => {
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky className={styles.tableHeader}>
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
