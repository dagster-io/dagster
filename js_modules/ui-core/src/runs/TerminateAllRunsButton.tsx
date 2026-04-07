import {Button} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import {useState} from 'react';

import {queuedStatuses} from './RunStatuses';
import {TerminateAllRunsDialog} from './TerminateAllRunsDialog';
import {RunsFilter} from '../graphql/types';

export const TerminateAllRunsButton = ({
  refetch,
  filter,
  disabled,
}: {
  refetch: () => void;
  filter: RunsFilter;
  disabled: boolean;
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <TerminateAllRunsDialog
        isOpen={isOpen}
        onClose={() => {
          setIsOpen(false);
          refetch();
        }}
        filter={filter}
        selectedRunsAllQueued={isEqual(filter, {statuses: Array.from(queuedStatuses)})}
      />
      <Button intent="danger" outlined disabled={disabled} onClick={() => setIsOpen(true)}>
        Terminate all…
      </Button>
    </>
  );
};
