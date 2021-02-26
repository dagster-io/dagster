import {useMutation} from '@apollo/client';
import {Colors, Switch, Tooltip} from '@blueprintjs/core';
import * as React from 'react';

import {useConfirmation} from 'src/app/CustomConfirmationProvider';
import {TickTag} from 'src/jobs/JobTick';
import {JobRunStatus} from 'src/jobs/JobUtils';
import {JobStateFragment} from 'src/jobs/types/JobStateFragment';
import {
  STOP_SCHEDULE_MUTATION,
  displayScheduleMutationErrors,
} from 'src/schedules/ScheduleMutations';
import {humanCronString} from 'src/schedules/humanCronString';
import {StopSchedule} from 'src/schedules/types/StopSchedule';
import {displaySensorMutationErrors, STOP_SENSOR_MUTATION} from 'src/sensors/SensorMutations';
import {StopSensor} from 'src/sensors/types/StopSensor';
import {JobType, JobStatus} from 'src/types/globalTypes';
import {Alert} from 'src/ui/Alert';
import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';
import {Table} from 'src/ui/Table';
import {Subheading} from 'src/ui/Text';
import {RepositoryOriginInformation} from 'src/workspace/RepositoryInformation';

export const UnloadableSensors: React.FunctionComponent<{
  sensorStates: JobStateFragment[];
}> = ({sensorStates}) => {
  if (!sensorStates.length) {
    return null;
  }
  return (
    <>
      <Subheading>Unloadable sensors</Subheading>
      <UnloadableSensorInfo />

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
  scheduleStates: JobStateFragment[];
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

const SensorStateRow = ({sensorState}: {sensorState: JobStateFragment}) => {
  const {id, name, status, repositoryOrigin, ticks} = sensorState;

  const [stopSensor, {loading: toggleOffInFlight}] = useMutation<StopSensor>(STOP_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
  });
  const [showRepositoryOrigin, setShowRepositoryOrigin] = React.useState(false);

  const onChangeSwitch = () => {
    if (status === JobStatus.RUNNING) {
      stopSensor({variables: {jobOriginId: id}});
    }
  };

  const latestTick = ticks.length ? ticks[0] : null;

  return (
    <tr key={name}>
      <td style={{width: 60}}>
        <Switch
          disabled={toggleOffInFlight || status === JobStatus.STOPPED}
          large
          innerLabelChecked="on"
          innerLabel="off"
          checked={status === JobStatus.RUNNING}
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
          <TickTag tick={latestTick} jobType={JobType.SENSOR} />
        ) : (
          <span style={{color: Colors.GRAY4}}>None</span>
        )}
      </td>
      <td>
        <div style={{display: 'flex'}}>
          <JobRunStatus jobState={sensorState} />
        </div>
      </td>
    </tr>
  );
};

const ScheduleStateRow: React.FunctionComponent<{
  scheduleState: JobStateFragment;
}> = ({scheduleState}) => {
  const [stopSchedule, {loading: toggleOffInFlight}] = useMutation<StopSchedule>(
    STOP_SCHEDULE_MUTATION,
    {
      onCompleted: displayScheduleMutationErrors,
    },
  );
  const [showRepositoryOrigin, setShowRepositoryOrigin] = React.useState(false);
  const confirm = useConfirmation();
  const {id, name, ticks, status, repositoryOrigin, jobSpecificData} = scheduleState;
  const latestTick = ticks.length > 0 ? ticks[0] : null;
  const cronSchedule =
    jobSpecificData && jobSpecificData.__typename === 'ScheduleJobData'
      ? jobSpecificData.cronSchedule
      : null;
  const onChangeSwitch = async () => {
    if (status === JobStatus.RUNNING) {
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
        <Switch
          checked={status === JobStatus.RUNNING}
          large={true}
          disabled={status !== JobStatus.RUNNING || toggleOffInFlight}
          innerLabelChecked="on"
          innerLabel="off"
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
            <Tooltip position={'bottom'} content={cronSchedule}>
              {humanCronString(cronSchedule)}
            </Tooltip>
          ) : (
            <div>&mdash;</div>
          )}
        </div>
      </td>
      <td>{latestTick ? <TickTag tick={latestTick} jobType={JobType.SCHEDULE} /> : null}</td>
      <td>
        <JobRunStatus jobState={scheduleState} />
      </td>
      <td>
        <div style={{display: 'flex'}}>&mdash;</div>
      </td>
    </tr>
  );
};
