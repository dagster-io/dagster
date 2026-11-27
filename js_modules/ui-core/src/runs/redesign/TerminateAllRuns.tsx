import {Button, Colors, Icon, Tooltip} from '@dagster-io/ui-components';
import {useContext, useId, useState} from 'react';

import {RunsFilter} from '../../graphql/types';
import {inProgressStatuses, queuedStatuses} from '../RunStatuses';
import {RunsQueryRefetchContext} from '../RunUtils';
import {TerminateAllRunsDialog} from '../TerminateAllRunsDialog';

const LABEL = 'Terminate all queued and in-progress runs';
const DISABLED_REASON = 'The filter excludes queued and in-progress runs';

const TERMINABLE_STATUSES = [...queuedStatuses, ...inProgressStatuses];

type TerminateAllRunsProps = {
  filter: RunsFilter;
};

export const TerminateAllRuns = ({filter}: TerminateAllRunsProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const {refetch} = useContext(RunsQueryRefetchContext);
  const reasonId = useId();

  const statuses = filter.statuses?.length
    ? filter.statuses.filter((status) => TERMINABLE_STATUSES.includes(status))
    : TERMINABLE_STATUSES;
  const isDisabled = statuses.length === 0;
  const allQueued = statuses.every((status) => queuedStatuses.has(status));

  return (
    <>
      <Tooltip content={isDisabled ? DISABLED_REASON : LABEL} position="bottom-end">
        <Button
          intent="none"
          icon={<Icon name="cancel" color={Colors.accentRed()} />}
          preserveIconColor
          disabled={isDisabled}
          aria-label={LABEL}
          aria-describedby={isDisabled ? reasonId : undefined}
          onClick={() => setIsOpen(true)}
        />
      </Tooltip>
      {isDisabled && (
        <span id={reasonId} hidden>
          {DISABLED_REASON}
        </span>
      )}
      <TerminateAllRunsDialog
        isOpen={isOpen}
        onClose={() => {
          setIsOpen(false);
          refetch();
        }}
        filter={{...filter, statuses}}
        selectedRunsAllQueued={allQueued}
      />
    </>
  );
};
