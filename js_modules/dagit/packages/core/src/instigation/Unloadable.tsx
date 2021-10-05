import {useMutation} from '@apollo/client';
import * as React from 'react';

import {useConfirmation} from '../app/CustomConfirmationProvider';
import {
  displayScheduleMutationErrors,
  STOP_SCHEDULE_MUTATION,
} from '../schedules/ScheduleMutations';
import {humanCronString} from '../schedules/humanCronString';
import {StopSchedule} from '../schedules/types/StopSchedule';
import {displaySensorMutationErrors, STOP_SENSOR_MUTATION} from '../sensors/SensorMutations';
import {StopSensor} from '../sensors/types/StopSensor';
import {InstigationStatus, InstigationType} from '../types/globalTypes';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {Checkbox} from '../ui/Checkbox';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {Table} from '../ui/Table';
import {Subheading} from '../ui/Text';
import {Tooltip} from '../ui/Tooltip';
import {RepositoryOriginInformation} from '../workspace/RepositoryInformation';

import {TickTag} from './InstigationTick';
import {InstigatedRunStatus} from './InstigationUtils';
import {InstigationStateFragment} from './types/InstigationStateFragment';

export const UnloadableSensors: React.FunctionComponent<{
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

export const UnloadableSchedules: React.FunctionComponent<{
  scheduleStates: InstigationStateFragment[];
}> = ({scheduleStates}) => {
  if (!scheduleStates.length) {
    return null;
  }
  return (
    <>
      <Subheading>Unloadable schedules</Subheading>
      <UnloadableScheduleInfo />
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
  const {id, name, status, repositoryOrigin, ticks} = sensorState;

  const [stopSensor, {loading: toggleOffInFlight}] = useMutation<StopSensor>(STOP_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
  });
  const [showRepositoryOrigin, setShowRepositoryOrigin] = React.useState(false);

  const onChangeSwitch = () => {
    if (status === InstigationStatus.RUNNING) {
      stopSensor({variables: {jobOriginId: id}});
    }
  };

  const latestTick = ticks.length ? ticks[0] : null;

  return (
    <tr key={name}>
      <td style={{width: 60}}>
        <Checkbox
          format="switch"
          disabled={toggleOffInFlight || status === InstigationStatus.STOPPED}
          checked={status === InstigationStatus.RUNNING}
          onChange={onChangeSwitch}
        />
      </td>
      <td>
        <Group direction="row" spacing={8} alignItems="center">
          {name}
          <ButtonLink
            onClick={() => {
              setShowRepositoryOrigin(!showRepositoryOrigin);
            }}
          >
            show info
          </ButtonLink>
        </Group>
        {showRepositoryOrigin && <RepositoryOriginInformation origin={repositoryOrigin} />}
      </td>
      <td>
        {latestTick ? (
          <TickTag tick={latestTick} instigationType={InstigationType.SENSOR} />
        ) : (
          <span style={{color: ColorsWIP.Gray300}}>None</span>
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

const ScheduleStateRow: React.FunctionComponent<{
  scheduleState: InstigationStateFragment;
}> = ({scheduleState}) => {
  const [stopSchedule, {loading: toggleOffInFlight}] = useMutation<StopSchedule>(
    STOP_SCHEDULE_MUTATION,
    {
      onCompleted: displayScheduleMutationErrors,
    },
  );
  const [showRepositoryOrigin, setShowRepositoryOrigin] = React.useState(false);
  const confirm = useConfirmation();
  const {id, name, ticks, status, repositoryOrigin, typeSpecificData} = scheduleState;
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
          'The schedule definition for this schedule is not available. ' +
          'If you turn off this schedule, you will not be able to turn it back on from ' +
          'the currently loaded workspace.',
      });
      stopSchedule({variables: {scheduleOriginId: id}});
    }
  };

  return (
    <tr key={name}>
      <td style={{width: 60}}>
        <Checkbox
          format="switch"
          checked={status === InstigationStatus.RUNNING}
          disabled={status !== InstigationStatus.RUNNING || toggleOffInFlight}
          onChange={onChangeSwitch}
        />
      </td>
      <td>
        <Group direction="row" spacing={8} alignItems="center">
          <div>{name}</div>
          <ButtonLink
            onClick={() => {
              setShowRepositoryOrigin(!showRepositoryOrigin);
            }}
          >
            show info
          </ButtonLink>
        </Group>
        {showRepositoryOrigin && <RepositoryOriginInformation origin={repositoryOrigin} />}
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
