import {Box, ButtonLink, Colors, Tag, Tooltip, FontFamily} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {ScheduleSwitch} from '../schedules/ScheduleSwitch';
import {humanCronString} from '../schedules/humanCronString';
import {ScheduleSwitchFragment} from '../schedules/types/ScheduleSwitchFragment';
import {SensorSwitch} from '../sensors/SensorSwitch';
import {SensorSwitchFragment} from '../sensors/types/SensorSwitchFragment';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {ScheduleAndSensorDialog} from './ScheduleAndSensorDialog';

export const ScheduleOrSensorTag: React.FC<{
  schedules: ScheduleSwitchFragment[];
  sensors: SensorSwitchFragment[];
  repoAddress: RepoAddress;
  showSwitch?: boolean;
}> = ({schedules, sensors, repoAddress, showSwitch = true}) => {
  const [open, setOpen] = React.useState(false);

  const scheduleCount = schedules.length;
  const sensorCount = sensors.length;

  if (scheduleCount > 1 || sensorCount > 1 || (scheduleCount && sensorCount)) {
    const buttonText =
      scheduleCount && sensorCount
        ? `View ${scheduleCount + sensorCount} schedules/sensors`
        : scheduleCount
        ? `View ${scheduleCount} schedules`
        : `View ${sensorCount} sensors`;

    const icon = scheduleCount > 1 ? 'schedule' : 'sensors';

    return (
      <>
        <Tag icon={icon}>
          <ButtonLink onClick={() => setOpen(true)} color={Colors.Link}>
            {buttonText}
          </ButtonLink>
        </Tag>
        <ScheduleAndSensorDialog
          isOpen={open}
          onClose={() => setOpen(false)}
          repoAddress={repoAddress}
          schedules={schedules}
          sensors={sensors}
          showSwitch={showSwitch}
        />
      </>
    );
  }

  if (scheduleCount) {
    return (
      <MatchingSchedule schedule={schedules[0]} repoAddress={repoAddress} showSwitch={showSwitch} />
    );
  }

  if (sensorCount) {
    return <MatchingSensor sensor={sensors[0]} repoAddress={repoAddress} showSwitch={showSwitch} />;
  }

  return null;
};

const MatchingSchedule: React.FC<{
  schedule: ScheduleSwitchFragment;
  repoAddress: RepoAddress;
  showSwitch: boolean;
}> = ({schedule, repoAddress, showSwitch}) => {
  const running = schedule.scheduleState.status === 'RUNNING';
  const tag = (
    <Tag intent={running ? 'primary' : 'none'} icon="schedule">
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        Schedule:
        <Link to={workspacePathFromAddress(repoAddress, `/schedules/${schedule.name}`)}>
          {humanCronString(schedule.cronSchedule)}
        </Link>
        {showSwitch ? (
          <ScheduleSwitch size="small" repoAddress={repoAddress} schedule={schedule} />
        ) : null}
      </Box>
    </Tag>
  );

  return schedule.cronSchedule ? (
    <Tooltip
      placement="bottom"
      content={
        <Box flex={{direction: 'column', gap: 4}}>
          <div>
            Name: <strong>{schedule.name}</strong>
          </div>
          <div>
            Cron:{' '}
            <span style={{fontFamily: FontFamily.monospace, marginLeft: '4px'}}>
              ({schedule.cronSchedule})
            </span>
          </div>
        </Box>
      }
    >
      {tag}
    </Tooltip>
  ) : (
    tag
  );
};

const MatchingSensor: React.FC<{
  sensor: SensorSwitchFragment;
  repoAddress: RepoAddress;
  showSwitch: boolean;
}> = ({sensor, repoAddress, showSwitch}) => {
  const running = sensor.sensorState.status === 'RUNNING';
  return (
    <Tag intent={running ? 'primary' : 'none'} icon="sensors">
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        Sensor:
        <Link to={workspacePathFromAddress(repoAddress, `/sensors/${sensor.name}`)}>
          {sensor.name}
        </Link>
        {showSwitch ? (
          <SensorSwitch size="small" repoAddress={repoAddress} sensor={sensor} />
        ) : null}
      </Box>
    </Tag>
  );
};
