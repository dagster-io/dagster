import {Button, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';

import {RESET_SCHEDULE_MUTATION, displayScheduleMutationErrors} from './ScheduleMutations';
import {
  ResetScheduleMutation,
  ResetScheduleMutationVariables,
} from './types/ScheduleMutations.types';
import {ScheduleFragment} from './types/ScheduleUtils.types';
import {useMutation} from '../apollo-client';
import {DEFAULT_DISABLED_REASON, usePermissionsForLocation} from '../app/Permissions';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
  schedule: ScheduleFragment;
}

export const ScheduleResetButton = ({repoAddress, schedule}: Props) => {
  const {
    permissions: {canStartSchedule, canStopRunningSchedule},
  } = usePermissionsForLocation(repoAddress.location);

  const {name} = schedule;
  const scheduleSelector = {
    ...repoAddressToSelector(repoAddress),
    scheduleName: name,
  };

  const [resetSchedule, {loading: toggleOnInFlight}] = useMutation<
    ResetScheduleMutation,
    ResetScheduleMutationVariables
  >(RESET_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });
  const onClick = () => {
    resetSchedule({variables: {scheduleSelector}});
  };

  const hasPermission = canStartSchedule && canStopRunningSchedule;
  const disabled = toggleOnInFlight || !hasPermission;
  const tooltipContent = hasPermission
    ? `In code, a default status for "${name}" has been set to "${schedule.defaultStatus}". Click here to reset the schedule status to track the status set in code.`
    : DEFAULT_DISABLED_REASON;

  return (
    <Tooltip
      content={<div style={{maxWidth: '500px', wordBreak: 'break-word'}}>{tooltipContent}</div>}
      display="flex"
    >
      <Button disabled={disabled} onClick={onClick}>
        Reset schedule status
      </Button>
    </Tooltip>
  );
};
