import {Box, ButtonLink, Caption, Checkbox, Colors, Mono, Tag} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {CreatedByTagCell} from './CreatedByTag';
import {RunGrouping} from './GroupedRunsRoot';
import {QueuedRunCriteriaDialog} from './QueuedRunCriteriaDialog';
import {RunActionsMenu} from './RunActionsMenu';
import {RunGroupingActionsMenu} from './RunGroupingActionsMenu';
import {RunRowTags} from './RunRowTags';
import {GroupStatusTagWithStats, RunStatusTagWithStats} from './RunStatusTag';
import {DagsterTag} from './RunTag';
import {RunTargetLink} from './RunTargetLink';
import {RunStateSummary, RunTime, titleForRun} from './RunUtils';
import {RunFilterToken} from './RunsFilterInput';
import {RunTableRunFragment} from './types/RunTable.types';
import {useResolveRunTarget} from './useResolveRunTarget';
import {RunStatus} from '../graphql/types';

export const GroupedRunRow = ({
  group,
  hasCheckboxColumn,
  canTerminateOrDelete,
  onAddTag,
  checked,
  onToggleChecked,
  additionalActionsForRun,
}: {
  group: RunGrouping;
  hasCheckboxColumn: boolean;
  canTerminateOrDelete: boolean;
  onAddTag?: (token: RunFilterToken) => void;
  checked?: boolean;
  onToggleChecked?: (values: {checked: boolean; shiftKey: boolean}) => void;
  additionalColumns?: React.ReactNode[];
  additionalActionsForRun?: (run: RunTableRunFragment) => React.ReactNode[];
  hideCreatedBy?: boolean;
}) => {
  const run = group.runs[0]!;

  const {isJob, repoAddressGuess} = useResolveRunTarget(run);

  const onChange = (e: React.FormEvent<HTMLInputElement>) => {
    if (e.target instanceof HTMLInputElement) {
      const {checked} = e.target;
      const shiftKey =
        e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
      onToggleChecked && onToggleChecked({checked, shiftKey});
    }
  };

  const isReexecution = run.tags.some((tag) => tag.key === DagsterTag.ParentRunId);

  const [showQueueCriteria, setShowQueueCriteria] = React.useState(false);
  const [isHovered, setIsHovered] = React.useState(false);

  const backfillId = run.tags.find((t) => t.key === DagsterTag.Backfill)?.value;
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
          <Link to={backfillId ? `/run-requests/b/${backfillId}?tab=runs` : `/runs/${run.id}`}>
            <Mono>
              {backfillId ? backfillId : titleForRun(run)} ({group.runs.length}{' '}
              {group.runs.length === 1 ? 'run' : 'runs'})
            </Mono>
          </Link>
          <Box
            flex={{direction: 'row', alignItems: 'center', wrap: 'wrap'}}
            style={{gap: '4px 8px', lineHeight: 0}}
          >
            <Tag>
              <Box flex={{direction: 'row', gap: 4}}>
                <RunTargetLink isJob={isJob} run={run} repoAddress={repoAddressGuess} />
              </Box>
            </Tag>
            <RunRowTags run={run} isJob={isJob} isHovered={isHovered} onAddTag={onAddTag} />

            {run.status === RunStatus.QUEUED ? (
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
        <Box flex={{direction: 'column', gap: 4}}>
          <RunTime run={run} />
          {isReexecution ? (
            <div>
              <Tag icon="cached">Re-execution</Tag>
            </div>
          ) : null}
        </Box>
      </td>
      <td>
        <CreatedByTagCell
          repoAddress={repoAddressGuess}
          tags={run.tags || []}
          onAddTag={onAddTag}
        />
      </td>
      <td>
        {group.runs.length > 1 ? (
          <GroupStatusTagWithStats group={group} />
        ) : (
          <RunStatusTagWithStats status={run.status} runId={run.id} />
        )}
      </td>
      <td>
        <RunStateSummary run={run} />
      </td>
      <td>
        <Box flex={{justifyContent: 'flex-end'}}>
          {group.runs.length > 1 ? (
            <RunGroupingActionsMenu group={group} />
          ) : (
            <RunActionsMenu
              run={run}
              onAddTag={onAddTag}
              additionalActionsForRun={additionalActionsForRun}
            />
          )}
        </Box>
      </td>
      <QueuedRunCriteriaDialog
        run={run}
        isOpen={showQueueCriteria}
        onClose={() => setShowQueueCriteria(false)}
      />
    </tr>
  );
};
