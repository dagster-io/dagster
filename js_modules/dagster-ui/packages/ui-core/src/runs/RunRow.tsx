import {Box, ButtonLink, Caption, Checkbox, Colors, Mono, Tag} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {CreatedByTagCell} from './CreatedByTag';
import {QueuedRunCriteriaDialog} from './QueuedRunCriteriaDialog';
import {RunActionsMenu} from './RunActionsMenu';
import {RunRowTags} from './RunRowTags';
import {RunStatusTagWithStats} from './RunStatusTag';
import {DagsterTag} from './RunTag';
import {RunTargetLink} from './RunTargetLink';
import {RunStateSummary, RunTime, titleForRun} from './RunUtils';
import {RunFilterToken} from './RunsFilterInput';
import {RunTableRunFragment} from './types/RunTableRunFragment.types';
import {useResolveRunTarget} from './useResolveRunTarget';
import {RunStatus} from '../graphql/types';

export const RunRow = ({
  run,
  hasCheckboxColumn,
  canTerminateOrDelete,
  onAddTag,
  checked,
  onToggleChecked,
  additionalColumns,
  isHighlighted,
  hideCreatedBy,
}: {
  run: RunTableRunFragment;
  hasCheckboxColumn: boolean;
  canTerminateOrDelete: boolean;
  onAddTag?: (token: RunFilterToken) => void;
  checked?: boolean;
  onToggleChecked?: (values: {checked: boolean; shiftKey: boolean}) => void;
  additionalColumns?: React.ReactNode[];
  isHighlighted?: boolean;
  hideCreatedBy?: boolean;
}) => {
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

  return (
    <Row
      highlighted={!!isHighlighted}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {hasCheckboxColumn ? (
        <td>
          {canTerminateOrDelete ? (
            <>{onToggleChecked ? <Checkbox checked={!!checked} onChange={onChange} /> : null}</>
          ) : null}
        </td>
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
        <RunActionsMenu run={run} onAddTag={onAddTag} />
      </td>
      <QueuedRunCriteriaDialog
        run={run}
        isOpen={showQueueCriteria}
        onClose={() => setShowQueueCriteria(false)}
      />
    </Row>
  );
};

const Row = styled.tr<{highlighted: boolean}>`
  ${({highlighted}) =>
    highlighted ? `box-shadow: inset 3px 3px #bfccd6, inset -3px -3px #bfccd6;` : null}
`;
