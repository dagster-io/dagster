import {useMutation} from '@apollo/client';
import {Checkbox, Tooltip} from '@dagster-io/ui';
import * as React from 'react';

import {usePermissionsForLocation} from '../app/Permissions';
import {graphql} from '../graphql';
import {InstigationStatus, ScheduleSwitchFragmentFragment} from '../graphql/graphql';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {
  displayScheduleMutationErrors,
  START_SCHEDULE_MUTATION,
  STOP_SCHEDULE_MUTATION,
} from './ScheduleMutations';

interface Props {
  repoAddress: RepoAddress;
  schedule: ScheduleSwitchFragmentFragment;
  size?: 'small' | 'large';
}

export const ScheduleSwitch: React.FC<Props> = (props) => {
  const {repoAddress, schedule, size = 'large'} = props;
  const {name, scheduleState} = schedule;
  const {status, id, selectorId} = scheduleState;

  const {canStartSchedule, canStopRunningSchedule} = usePermissionsForLocation(
    repoAddress.location,
  );

  const [startSchedule, {loading: toggleOnInFlight}] = useMutation(START_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });
  const [stopSchedule, {loading: toggleOffInFlight}] = useMutation(STOP_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });

  const scheduleSelector = {
    ...repoAddressToSelector(repoAddress),
    scheduleName: name,
  };

  const onStatusChange = () => {
    if (status === InstigationStatus.RUNNING) {
      stopSchedule({
        variables: {scheduleOriginId: id, scheduleSelectorId: selectorId},
      });
    } else {
      startSchedule({
        variables: {scheduleSelector},
      });
    }
  };

  const running = status === InstigationStatus.RUNNING;

  if (canStartSchedule.enabled && canStopRunningSchedule.enabled) {
    return (
      <Checkbox
        format="switch"
        checked={running || toggleOnInFlight}
        disabled={toggleOffInFlight || toggleOnInFlight}
        onChange={onStatusChange}
        size={size}
      />
    );
  }

  const lacksPermission =
    (running && !canStopRunningSchedule.enabled) || (!running && !canStartSchedule.enabled);
  const disabled = toggleOffInFlight || toggleOnInFlight || lacksPermission;

  const switchElement = (
    <Checkbox
      format="switch"
      checked={running || toggleOnInFlight}
      disabled={disabled}
      onChange={onStatusChange}
      size={size}
    />
  );

  if (!lacksPermission) {
    return switchElement;
  }

  const disabledReason = running
    ? canStopRunningSchedule.disabledReason
    : canStartSchedule.disabledReason;

  return (
    <Tooltip content={disabledReason} display="flex">
      {switchElement}
    </Tooltip>
  );
};

export const SCHEDULE_SWITCH_FRAGMENT = graphql(`
  fragment ScheduleSwitchFragment on Schedule {
    id
    name
    cronSchedule
    executionTimezone
    scheduleState {
      id
      selectorId
      status
    }
  }
`);
