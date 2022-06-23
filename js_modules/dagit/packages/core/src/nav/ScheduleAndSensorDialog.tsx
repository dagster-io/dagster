import {Box, Button, Dialog, DialogFooter, Subheading, Table} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {ScheduleSwitch} from '../schedules/ScheduleSwitch';
import {humanCronString} from '../schedules/humanCronString';
import {ScheduleSwitchFragment} from '../schedules/types/ScheduleSwitchFragment';
import {SensorSwitch} from '../sensors/SensorSwitch';
import {SensorSwitchFragment} from '../sensors/types/SensorSwitchFragment';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  repoAddress: RepoAddress;
  schedules: ScheduleSwitchFragment[];
  sensors: SensorSwitchFragment[];
  showSwitch?: boolean;
}

export const ScheduleAndSensorDialog = ({
  isOpen,
  onClose,
  repoAddress,
  schedules,
  sensors,
  showSwitch,
}: Props) => {
  const scheduleCount = schedules.length;
  const sensorCount = sensors.length;

  const dialogTitle =
    scheduleCount && sensorCount
      ? 'Schedules and sensors'
      : scheduleCount
      ? 'Schedules'
      : 'Sensors';

  return (
    <Dialog
      title={dialogTitle}
      canOutsideClickClose
      canEscapeKeyClose
      isOpen={isOpen}
      style={{width: '50vw', minWidth: '600px', maxWidth: '800px'}}
      onClose={onClose}
    >
      <Box padding={{bottom: 12}}>
        {scheduleCount ? (
          <>
            {sensorCount ? (
              <Box padding={{vertical: 16, horizontal: 24}}>
                <Subheading>Schedules ({scheduleCount})</Subheading>
              </Box>
            ) : null}
            <Table>
              <thead>
                <tr>
                  {showSwitch ? <th style={{width: '80px'}} /> : null}
                  <th>Schedule name</th>
                  <th>Schedule</th>
                </tr>
              </thead>
              <tbody>
                {schedules.map((schedule) => (
                  <tr key={schedule.name}>
                    {showSwitch ? (
                      <td>
                        <ScheduleSwitch repoAddress={repoAddress} schedule={schedule} />
                      </td>
                    ) : null}
                    <td>
                      <Link
                        to={workspacePathFromAddress(repoAddress, `/schedules/${schedule.name}`)}
                      >
                        {schedule.name}
                      </Link>
                    </td>
                    <td>
                      {humanCronString(schedule.cronSchedule, schedule.executionTimezone || 'UTC')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </>
        ) : null}
        {sensorCount ? (
          <>
            {scheduleCount ? (
              <Box padding={{vertical: 16, horizontal: 24}}>
                <Subheading>Sensors ({sensorCount})</Subheading>
              </Box>
            ) : null}
            <Table>
              <thead>
                <tr>
                  {showSwitch ? <th style={{width: '80px'}} /> : null}
                  <th>Sensor name</th>
                </tr>
              </thead>
              <tbody>
                {sensors.map((sensor) => (
                  <tr key={sensor.name}>
                    {showSwitch ? (
                      <td>
                        <SensorSwitch repoAddress={repoAddress} sensor={sensor} />
                      </td>
                    ) : null}
                    <td>
                      <Link to={workspacePathFromAddress(repoAddress, `/sensors/${sensor.name}`)}>
                        {sensor.name}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </>
        ) : null}
      </Box>
      <DialogFooter>
        <Button intent="primary" onClick={onClose}>
          OK
        </Button>
      </DialogFooter>
    </Dialog>
  );
};
