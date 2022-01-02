import {gql, useMutation} from '@apollo/client';
import * as React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {InstigationStatus} from '../types/globalTypes';
import {Checkbox} from '../ui/Checkbox';
import {Tooltip} from '../ui/Tooltip';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {
  displayScheduleMutationErrors,
  START_SCHEDULE_MUTATION,
  STOP_SCHEDULE_MUTATION,
} from './ScheduleMutations';
import {ScheduleSwitchFragment} from './types/ScheduleSwitchFragment';
import {StartSchedule} from './types/StartSchedule';
import {StopSchedule} from './types/StopSchedule';

interface Props {
  repoAddress: RepoAddress;
  schedule: ScheduleSwitchFragment;
  size?: 'small' | 'large';
}

export const ScheduleSwitch: React.FC<Props> = (props) => {
  const {repoAddress, schedule, size = 'large'} = props;
  const {name, scheduleState} = schedule;
  const {status, id, canChangeStatus} = scheduleState;

  const {canStartSchedule, canStopRunningSchedule} = usePermissions();

  const [startSchedule, {loading: toggleOnInFlight}] = useMutation<StartSchedule>(
    START_SCHEDULE_MUTATION,
    {
      onCompleted: displayScheduleMutationErrors,
    },
  );
  const [stopSchedule, {loading: toggleOffInFlight}] = useMutation<StopSchedule>(
    STOP_SCHEDULE_MUTATION,
    {
      onCompleted: displayScheduleMutationErrors,
    },
  );

  const scheduleSelector = {
    ...repoAddressToSelector(repoAddress),
    scheduleName: name,
  };

  const onStatusChange = () => {
    if (status === InstigationStatus.RUNNING) {
      stopSchedule({
        variables: {scheduleOriginId: id},
      });
    } else {
      startSchedule({
        variables: {scheduleSelector},
      });
    }
  };

  const running = status === InstigationStatus.RUNNING;

  if (canStartSchedule && canStopRunningSchedule && canChangeStatus) {
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

  const lacksPermission = (running && !canStopRunningSchedule) || (!running && !canStartSchedule);
  const disabled = !canChangeStatus || toggleOffInFlight || toggleOnInFlight || lacksPermission;

  const switchElement = (
    <Checkbox
      format="switch"
      checked={running || toggleOnInFlight}
      disabled={disabled}
      onChange={onStatusChange}
      size={size}
    />
  );

  let tooltip = null;
  if (!canChangeStatus) {
    if (running) {
      tooltip =
        'Schedule is set as running in code. To stop it, set its status to ScheduleStatus.STOPPED in code.';
    } else {
      tooltip =
        'Schedule is set as stopped in code. To stop it, set its status to ScheduleStatus.RUNNING in code.';
    }
  } else if (lacksPermission) {
    tooltip = DISABLED_MESSAGE;
  }

  return tooltip ? <Tooltip content={tooltip}>{switchElement}</Tooltip> : switchElement;
};

export const SCHEDULE_SWITCH_FRAGMENT = gql`
  fragment ScheduleSwitchFragment on Schedule {
    id
    name
    cronSchedule
    scheduleState {
      id
      status
      canChangeStatus
    }
  }
`;
