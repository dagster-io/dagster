import {Box, ButtonLink, Caption, Checkbox, Colors, Mono, Tag} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {CreatedByTagCell} from './CreatedByTag';
import {RunActionsMenu} from './RunActionsMenu';
import {RunRowTags} from './RunRowTags';
import {RunStatusTagWithStats} from './RunStatusTag';
import {DagsterTag} from './RunTag';
import {RunTargetLink} from './RunTargetLink';
import {RunStateSummary, RunTime} from './RunUtils';
import {RunFilterToken} from './RunsFilterInput';
import {RunTimeFragment} from './types/RunUtils.types';
import {RunsFeedTableEntryFragment} from './types/RunsFeedTable.types';
import {RunStatus} from '../graphql/types';
import {BackfillActionsMenu, backfillCanCancelRuns} from '../instance/backfill/BackfillActionsMenu';
import {BackfillTarget} from '../instance/backfill/BackfillRow';

export const RunsFeedRow = ({
  entry,
  hasCheckboxColumn,
  canTerminateOrDelete,
  onAddTag,
  checked,
  onToggleChecked,
  refetch,
}: {
  entry: RunsFeedTableEntryFragment;
  hasCheckboxColumn: boolean;
  canTerminateOrDelete: boolean;
  refetch: () => void;
  onAddTag?: (token: RunFilterToken) => void;
  checked?: boolean;
  onToggleChecked?: (values: {checked: boolean; shiftKey: boolean}) => void;
  additionalColumns?: React.ReactNode[];
  hideCreatedBy?: boolean;
}) => {
  const onChange = (e: React.FormEvent<HTMLInputElement>) => {
    if (e.target instanceof HTMLInputElement) {
      const {checked} = e.target;
      const shiftKey =
        e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
      onToggleChecked && onToggleChecked({checked, shiftKey});
    }
  };

  const isReexecution = entry.tags.some((tag) => tag.key === DagsterTag.ParentRunId);

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

  return (
    <tr onMouseEnter={() => setIsHovered(true)} onMouseLeave={() => setIsHovered(false)}>
      {hasCheckboxColumn ? (
        <td>
          {canTerminateOrDelete ? (
            <>{onToggleChecked ? <Checkbox checked={!!checked} onChange={onChange} /> : null}</>
          ) : null}
        </td>
      ) : null}
      <td>
        <Box flex={{direction: 'column', gap: 5}}>
          <Link
            to={
              entry.__typename === 'PartitionBackfill'
                ? `/runs-feed/b/${entry.id}?tab=runs`
                : `/runs/${entry.id}`
            }
          >
            <Mono>{entry.id}</Mono>
          </Link>
          <Box
            flex={{direction: 'row', alignItems: 'center', wrap: 'wrap'}}
            style={{gap: '4px 8px', lineHeight: 0}}
          >
            <RunRowTags
              run={{...entry, mode: ''}}
              isJob={true}
              isHovered={isHovered}
              onAddTag={onAddTag}
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
      </td>
      <td>
        <Tag>
          <Box flex={{direction: 'row', gap: 4}}>
            {entry.__typename === 'Run' ? (
              <RunTargetLink
                isJob={true}
                run={{...entry, pipelineName: entry.jobName!, stepKeysToExecute: []}}
                repoAddress={null}
              />
            ) : (
              <BackfillTarget backfill={entry} repoAddress={null} />
            )}
          </Box>
        </Tag>
      </td>
      <td>
        <CreatedByTagCell tags={entry.tags || []} onAddTag={onAddTag} />
      </td>
      <td>
        <RunStatusTagWithStats status={entry.runStatus} runId={entry.id} />
      </td>
      <td>
        <Box flex={{direction: 'column', gap: 4}}>
          <RunTime run={runTime} />
          {isReexecution ? (
            <div>
              <Tag icon="cached">Re-execution</Tag>
            </div>
          ) : null}
        </Box>
      </td>
      <td>
        <RunStateSummary run={runTime} />
      </td>
      <td>
        <Box flex={{justifyContent: 'flex-end'}}>
          {entry.__typename === 'PartitionBackfill' ? (
            <BackfillActionsMenu
              backfill={{...entry, status: entry.backfillStatus}}
              canCancelRuns={backfillCanCancelRuns(entry, entry.numCancelable > 0)}
              refetch={refetch}
              anchorLabel="View run"
            />
          ) : (
            <RunActionsMenu
              run={entry}
              // onAddTag={onAddTag}
            />
          )}
        </Box>
      </td>
      {/* <QueuedRunCriteriaDialog
        run={run}
        isOpen={showQueueCriteria}
        onClose={() => setShowQueueCriteria(false)}
      /> */}
    </tr>
  );
};
