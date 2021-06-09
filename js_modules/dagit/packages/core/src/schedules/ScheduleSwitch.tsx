import {useMutation} from '@apollo/client';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {JobStatus} from '../types/globalTypes';
import {SwitchWithoutLabel} from '../ui/SwitchWithoutLabel';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {
  displayScheduleMutationErrors,
  START_SCHEDULE_MUTATION,
  STOP_SCHEDULE_MUTATION,
} from './ScheduleMutations';
import {ScheduleFragment} from './types/ScheduleFragment';
import {StartSchedule} from './types/StartSchedule';
import {StopSchedule} from './types/StopSchedule';

interface Props {
  repoAddress: RepoAddress;
  schedule: ScheduleFragment;
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
    if (status === JobStatus.RUNNING) {
      stopSchedule({
        variables: {scheduleOriginId: id},
      });
    } else {
      startSchedule({
        variables: {scheduleSelector},
      });
    }
  };

  const running = status === JobStatus.RUNNING;

  if (canStartSchedule && canStopRunningSchedule) {
    return (
      <SwitchWithoutLabel
        checked={running || toggleOnInFlight}
        large
        disabled={toggleOffInFlight || toggleOnInFlight}
        innerLabelChecked="on"
        innerLabel="off"
        onChange={onStatusChange}
      />
    );
  }

  const lacksPermission = (running && !canStopRunningSchedule) || (!running && !canStartSchedule);
  const disabled = toggleOffInFlight || toggleOnInFlight || lacksPermission;

  return (
    <Tooltip content={lacksPermission ? DISABLED_MESSAGE : undefined}>
      <SwitchWithoutLabel
        checked={running || toggleOnInFlight}
        large
        disabled={disabled}
        innerLabelChecked="on"
        innerLabel="off"
        onChange={onStatusChange}
      />
    </Tooltip>
  );
};
