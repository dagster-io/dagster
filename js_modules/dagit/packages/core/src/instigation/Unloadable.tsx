import {useMutation} from '@apollo/client';
import {Alert, Box, Checkbox, Colors, Group, Table, Subheading, Tooltip} from '@dagster-io/ui';
import * as React from 'react';

import {useConfirmation} from '../app/CustomConfirmationProvider';
import {usePermissions} from '../app/Permissions';
import {
  displayScheduleMutationErrors,
  STOP_SCHEDULE_MUTATION,
} from '../schedules/ScheduleMutations';
import {humanCronString} from '../schedules/humanCronString';
import {StopSchedule, StopScheduleVariables} from '../schedules/types/StopSchedule';
import {displaySensorMutationErrors, STOP_SENSOR_MUTATION} from '../sensors/SensorMutations';
import {StopSensor, StopSensorVariables} from '../sensors/types/StopSensor';
import {InstigationStatus, InstigationType} from '../types/globalTypes';
import {InstigatorSelectorInformation} from '../workspace/RepositoryInformation';

import {TickTag} from './InstigationTick';
import {InstigatedRunStatus} from './InstigationUtils';
import {InstigationStateFragment} from './types/InstigationStateFragment';

export const UnloadableSensors: React.FC<{
  sensorStates: InstigationStateFragment[];
}> = ({sensorStates}) => {
  if (!sensorStates.length) {
    return null;
  }
  return (
    <>
      <Box padding={{top: 16, horizontal: 24}}>
        <Subheading>Unloadable sensors</Subheading>
        <UnloadableSensorInfo />
      </Box>
      <Table>
        <thead>
          <tr>
            <th style={{maxWidth: '60px'}}></th>
            <th>Sensor Name</th>
            <th style={{width: '100px'}}>Last Tick</th>
            <th>Last Run</th>
          </tr>
        </thead>
        <tbody>
          {sensorStates.map((sensorState) => (
            <SensorStateRow sensorState={sensorState} key={sensorState.id} />
          ))}
        </tbody>
      </Table>
    </>
  );
};

export const UnloadableSchedules: React.FC<{
  scheduleStates: InstigationStateFragment[];
}> = ({scheduleStates}) => {
  if (!scheduleStates.length) {
    return null;
  }
  return (
    <>
      <Box padding={{top: 16, horizontal: 24}}>
        <Subheading>Unloadable schedules</Subheading>
        <UnloadableScheduleInfo />
      </Box>
      <Table>
        <thead>
          <tr>
            <th style={{maxWidth: '60px'}}></th>
            <th>Schedule Name</th>
            <th style={{width: '150px'}}>Schedule</th>
            <th style={{width: '100px'}}>Last Tick</th>
            <th>Last Run</th>
            <th>Partition Set Status</th>
          </tr>
        </thead>
        <tbody>
          {scheduleStates.map((scheduleState) => (
            <ScheduleStateRow scheduleState={scheduleState} key={scheduleState.id} />
          ))}
        </tbody>
      </Table>
    </>
  );
};

const UnloadableSensorInfo = () => (
  <Box margin={{vertical: 20}}>
    <Alert
      intent="warning"
      title={
        <div>
          Note: You can turn off any of the following sensors, but you cannot turn them back on.{' '}
        </div>
      }
      description={
        <div>
          The following sensors were previously started but now cannot be loaded. They may be part
          of a different workspace or from a sensor or repository that no longer exists in code. You
          can turn them off, but you cannot turn them back on since they can’t be loaded.
        </div>
      }
    />
  </Box>
);

const UnloadableScheduleInfo = () => (
  <Box margin={{vertical: 20}}>
    <Alert
      intent="warning"
      title={
        <div>
          Note: You can turn off any of the following schedules, but you cannot turn them back on.
        </div>
      }
      description={
        <div>
          The following schedules were previously started but now cannot be loaded. They may be part
          of a different workspace or from a schedule or repository that no longer exists in code.
          You can turn them off, but you cannot turn them back on since they can’t be loaded.
        </div>
      }
    />
  </Box>
);

const SensorStateRow = ({sensorState}: {sensorState: InstigationStateFragment}) => {
  const {id, selectorId, name, status, ticks} = sensorState;
  const {canStopSensor} = usePermissions();

  const [stopSensor, {loading: toggleOffInFlight}] = useMutation<StopSensor, StopSensorVariables>(
    STOP_SENSOR_MUTATION,
    {
      onCompleted: displaySensorMutationErrors,
    },
  );
  const confirm = useConfirmation();

  const onChangeSwitch = async () => {
    if (status === InstigationStatus.RUNNING) {
      await confirm({
        title: 'Are you sure you want to turn off this sensor?',
        description:
          'The definition for this sensor is not available. ' +
          'If you turn it off, you will not be able to turn it back on from ' +
          'the currently loaded workspace.',
      });
      stopSensor({variables: {jobOriginId: id, jobSelectorId: selectorId}});
    }
  };

  const lacksPermission = status === InstigationStatus.RUNNING && !canStopSensor.enabled;
  const latestTick = ticks.length ? ticks[0] : null;

  const checkbox = () => {
    const element = (
      <Checkbox
        format="switch"
        disabled={toggleOffInFlight || status === InstigationStatus.STOPPED || lacksPermission}
        checked={status === InstigationStatus.RUNNING}
        onChange={onChangeSwitch}
      />
    );
    return lacksPermission ? (
      <Tooltip content={canStopSensor.disabledReason}>{element}</Tooltip>
    ) : (
      element
    );
  };

  return (
    <tr key={name}>
      <td style={{width: 60}}>{checkbox()}</td>
      <td>
        <Group direction="row" spacing={8} alignItems="center">
          {name}
        </Group>
        <InstigatorSelectorInformation instigatorState={sensorState} />
      </td>
      <td>
        {latestTick ? (
          <TickTag tick={latestTick} instigationType={InstigationType.SENSOR} />
        ) : (
          <span style={{color: Colors.Gray300}}>None</span>
        )}
      </td>
      <td>
        <div style={{display: 'flex'}}>
          <InstigatedRunStatus instigationState={sensorState} />
        </div>
      </td>
    </tr>
  );
};

const ScheduleStateRow: React.FC<{
  scheduleState: InstigationStateFragment;
}> = ({scheduleState}) => {
  const {canStopRunningSchedule} = usePermissions();
  const [stopSchedule, {loading: toggleOffInFlight}] = useMutation<
    StopSchedule,
    StopScheduleVariables
  >(STOP_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });
  const confirm = useConfirmation();
  const {id, selectorId, name, ticks, status, typeSpecificData} = scheduleState;
  const latestTick = ticks.length > 0 ? ticks[0] : null;
  const cronSchedule =
    typeSpecificData && typeSpecificData.__typename === 'ScheduleData'
      ? typeSpecificData.cronSchedule
      : null;
  const onChangeSwitch = async () => {
    if (status === InstigationStatus.RUNNING) {
      await confirm({
        title: 'Are you sure you want to stop this schedule?',
        description:
          'The definition for this schedule is not available. ' +
          'If you turn it off, you will not be able to turn it back on from ' +
          'the currently loaded workspace.',
      });
      stopSchedule({variables: {scheduleOriginId: id, scheduleSelectorId: selectorId}});
    }
  };

  const lacksPermission = status === InstigationStatus.RUNNING && !canStopRunningSchedule.enabled;
  const checkbox = () => {
    const element = (
      <Checkbox
        format="switch"
        checked={status === InstigationStatus.RUNNING}
        disabled={status !== InstigationStatus.RUNNING || toggleOffInFlight || lacksPermission}
        onChange={onChangeSwitch}
      />
    );

    return lacksPermission ? (
      <Tooltip content={canStopRunningSchedule.disabledReason}>{element}</Tooltip>
    ) : (
      element
    );
  };

  return (
    <tr key={name}>
      <td style={{width: 60}}>{checkbox()}</td>
      <td>
        <Group direction="row" spacing={8} alignItems="center">
          <div>{name}</div>
        </Group>
        <InstigatorSelectorInformation instigatorState={scheduleState} />
      </td>
      <td style={{maxWidth: 150}}>
        <div
          style={{
            position: 'relative',
            width: '100%',
            whiteSpace: 'pre-wrap',
            display: 'block',
          }}
        >
          {cronSchedule ? (
            <Tooltip position="bottom" content={cronSchedule}>
              {humanCronString(cronSchedule)}
            </Tooltip>
          ) : (
            <div>&mdash;</div>
          )}
        </div>
      </td>
      <td>
        {latestTick ? (
          <TickTag tick={latestTick} instigationType={InstigationType.SCHEDULE} />
        ) : null}
      </td>
      <td>
        <InstigatedRunStatus instigationState={scheduleState} />
      </td>
      <td>
        <div style={{display: 'flex'}}>&mdash;</div>
      </td>
    </tr>
  );
};
