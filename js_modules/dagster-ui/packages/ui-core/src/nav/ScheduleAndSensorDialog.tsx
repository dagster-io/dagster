import {Box, Button, Dialog, DialogFooter, Subheading, Table} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {ScheduleSwitch} from '../schedules/ScheduleSwitch';
import {humanCronString} from '../schedules/humanCronString';
import {ScheduleSwitchFragment} from '../schedules/types/ScheduleSwitchFragment.types';
import {SensorSwitch} from '../sensors/SensorSwitch';
import {SensorSwitchFragment} from '../sensors/types/SensorSwitchFragment.types';
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
      ? '调度和传感器'
      : scheduleCount
        ? '调度'
        : '传感器';

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
                <Subheading>调度 ({scheduleCount})</Subheading>
              </Box>
            ) : null}
            <Table>
              <thead>
                <tr>
                  {showSwitch ? <th style={{width: '80px'}} /> : null}
                  <th>调度名称</th>
                  <th>调度</th>
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
                      {humanCronString(schedule.cronSchedule, {
                        longTimezoneName: schedule.executionTimezone || 'UTC',
                      })}
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
                <Subheading>传感器 ({sensorCount})</Subheading>
              </Box>
            ) : null}
            <Table>
              <thead>
                <tr>
                  {showSwitch ? <th style={{width: '80px'}} /> : null}
                  <th>传感器名称</th>
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
          确定
        </Button>
      </DialogFooter>
    </Dialog>
  );
};
