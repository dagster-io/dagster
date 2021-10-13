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
}

export const ScheduleSwitch: React.FC<Props> = (props) => {
  const {repoAddress, schedule} = props;
  const {name, scheduleState} = schedule;
  const {status, id} = scheduleState;

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

  if (canStartSchedule && canStopRunningSchedule) {
    return (
      <Checkbox
        format="switch"
        checked={running || toggleOnInFlight}
        disabled={toggleOffInFlight || toggleOnInFlight}
        onChange={onStatusChange}
      />
    );
  }

  const lacksPermission = (running && !canStopRunningSchedule) || (!running && !canStartSchedule);
  const disabled = toggleOffInFlight || toggleOnInFlight || lacksPermission;

  const switchElement = (
    <Checkbox
      format="switch"
      checked={running || toggleOnInFlight}
      disabled={disabled}
      onChange={onStatusChange}
    />
  );

  return lacksPermission ? (
    <Tooltip content={DISABLED_MESSAGE}>{switchElement}</Tooltip>
  ) : (
    switchElement
  );
};

export const SCHEDULE_SWITCH_FRAGMENT = gql`
  fragment ScheduleSwitchFragment on Schedule {
    id
    name
    scheduleState {
      id
      status
    }
  }
`;
