import {Box, ButtonLink, Colors, Tag, Tooltip, FontFamily, MiddleTruncate} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {ScheduleSwitch} from '../schedules/ScheduleSwitch';
import {humanCronString} from '../schedules/humanCronString';
import {ScheduleSwitchFragment} from '../schedules/types/ScheduleSwitch.types';
import {SensorSwitch} from '../sensors/SensorSwitch';
import {SensorSwitchFragment} from '../sensors/types/SensorSwitch.types';
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
        ? `${scheduleCount + sensorCount} schedules/sensors`
        : scheduleCount
        ? `${scheduleCount} schedules`
        : `${sensorCount} sensors`;

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
  const {cronSchedule, executionTimezone, scheduleState} = schedule;
  const running = scheduleState.status === 'RUNNING';
  const tag = (
    <Tag intent={running ? 'primary' : 'none'} icon="schedule">
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        <Link
          to={workspacePathFromAddress(repoAddress, `/schedules/${schedule.name}`)}
          style={{overflow: 'hidden', textOverflow: 'ellipsis'}}
        >
          {humanCronString(cronSchedule, executionTimezone || 'UTC')}
        </Link>
        {showSwitch ? (
          <ScheduleSwitch size="small" repoAddress={repoAddress} schedule={schedule} />
        ) : null}
      </Box>
    </Tag>
  );

  return schedule.cronSchedule ? (
    <Tooltip
      placement="top-start"
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
          <div>
            Timezone: <strong>{schedule.executionTimezone || 'UTC'}</strong>
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
        <Link
          to={workspacePathFromAddress(repoAddress, `/sensors/${sensor.name}`)}
          style={{maxWidth: 200, overflow: 'hidden'}}
        >
          <MiddleTruncate text={sensor.name} />
        </Link>
        {showSwitch ? (
          <SensorSwitch size="small" repoAddress={repoAddress} sensor={sensor} />
        ) : null}
      </Box>
    </Tag>
  );
};
