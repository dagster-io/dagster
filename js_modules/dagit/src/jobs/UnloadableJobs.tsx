import {useMutation} from '@apollo/client';
import {Button, Callout, Intent, Colors, Switch, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {useConfirmation} from 'src/CustomConfirmationProvider';
import {TickTag} from 'src/JobTick';
import {RepositoryOriginInformation} from 'src/RepositoryInformation';
import {RunStatus} from 'src/runs/RunStatusDots';
import {titleForRun} from 'src/runs/RunUtils';
import {
  STOP_SCHEDULE_MUTATION,
  displayScheduleMutationErrors,
} from 'src/schedules/ScheduleMutations';
import {humanCronString} from 'src/schedules/humanCronString';
import {StopSchedule} from 'src/schedules/types/StopSchedule';
import {displaySensorMutationErrors, STOP_SENSOR_MUTATION} from 'src/sensors/SensorMutations';
import {JobStateFragment} from 'src/sensors/types/JobStateFragment';
import {StopSensor} from 'src/sensors/types/StopSensor';
import {JobType, JobStatus} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';
import {Table} from 'src/ui/Table';
import {Heading} from 'src/ui/Text';

const NUM_RUNS_TO_DISPLAY = 10;

export const UnloadableJobs: React.FunctionComponent<{
  jobStates: JobStateFragment[];
  jobType?: JobType;
}> = ({jobStates, jobType}) => {
  if (!jobStates.length) {
    return null;
  }
  const unloadableSchedules = jobStates.filter((state) => state.jobType === JobType.SCHEDULE);
  const unloadableSensors = jobStates.filter((state) => state.jobType === JobType.SENSOR);
  if (jobType === JobType.SENSOR) {
    return unloadableSensors.length ? <UnloadableSensors sensorStates={unloadableSensors} /> : null;
  }
  if (jobType === JobType.SCHEDULE) {
    return unloadableSchedules.length ? (
      <UnloadableSchedules scheduleStates={unloadableSchedules} />
    ) : null;
  }
  return (
    <Group direction="vertical" spacing={8}>
      <Box
        flex={{justifyContent: 'space-between', alignItems: 'flex-end'}}
        padding={{bottom: 12}}
        border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
      >
        <Heading>Unloadable</Heading>
      </Box>
      {unloadableSchedules.length ? (
        <UnloadableSchedules scheduleStates={unloadableSchedules} />
      ) : null}
      {unloadableSensors.length ? <UnloadableSensors sensorStates={unloadableSensors} /> : null}
    </Group>
  );
};

const UnloadableSensors: React.FunctionComponent<{
  sensorStates: JobStateFragment[];
}> = ({sensorStates}) => {
  return (
    <>
      <h3>Unloadable sensors:</h3>
      <UnloadableSensorInfo />

      <Table striped style={{width: '100%'}}>
        <thead>
          <tr>
            <th style={{maxWidth: '60px'}}></th>
            <th>Sensor Name</th>
            <th></th>
            <th style={{width: '100px'}}>Last Tick</th>
            <th>Latest Runs</th>
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

const UnloadableSchedules: React.FunctionComponent<{
  scheduleStates: JobStateFragment[];
}> = ({scheduleStates}) => {
  return (
    <>
      <h3>Unloadable schedules:</h3>
      <UnloadableScheduleInfo />

      <Table striped style={{width: '100%'}}>
        <thead>
          <tr>
            <th style={{maxWidth: '60px'}}></th>
            <th>Schedule Name</th>
            <th style={{width: '150px'}}>Schedule</th>
            <th style={{width: '100px'}}>Last Tick</th>
            <th>Latest Runs</th>
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

const UnloadableSensorInfo = () => {
  const [showMore, setShowMore] = React.useState(false);

  return (
    <Callout style={{marginBottom: 20}} intent={Intent.WARNING}>
      <div style={{display: 'flex', justifyContent: 'space-between'}}>
        <h4 style={{margin: 0}}>
          Note: You can turn off any of the following sensors, but you cannot turn them back on.{' '}
        </h4>

        {!showMore && (
          <Button small={true} onClick={() => setShowMore(true)}>
            Show more info
          </Button>
        )}
      </div>

      {showMore && (
        <div style={{marginTop: 10}}>
          <p>
            The following sensors were previously started but now cannot be loaded. They may be part
            of a different workspace or from a sensor or repository that no longer exists in code.
            You can turn them off, but you cannot turn them back on since they can’t be loaded.
          </p>
        </div>
      )}
    </Callout>
  );
};

const UnloadableScheduleInfo = () => {
  const [showMore, setShowMore] = React.useState(false);

  return (
    <Callout style={{marginBottom: 20}} intent={Intent.WARNING}>
      <div style={{display: 'flex', justifyContent: 'space-between'}}>
        <h4 style={{margin: 0}}>
          Note: You can turn off any of the following schedules, but you cannot turn them back on.{' '}
        </h4>

        {!showMore && (
          <Button small={true} onClick={() => setShowMore(true)}>
            Show more info
          </Button>
        )}
      </div>

      {showMore && (
        <div style={{marginTop: 10}}>
          <p>
            The following schedules were previously started but now cannot be loaded. They may be
            part of a different workspace or from a schedule or repository that no longer exists in
            code. You can turn them off, but you cannot turn them back on since they can’t be
            loaded.
          </p>
        </div>
      )}
    </Callout>
  );
};

const SensorStateRow = ({sensorState}: {sensorState: JobStateFragment}) => {
  const {id, name, status, repositoryOrigin, runs, ticks} = sensorState;

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
        <Group direction="horizontal" spacing={8} alignItems="center">
          {name}
          <ButtonLink
            onClick={() => {
              setShowRepositoryOrigin(!showRepositoryOrigin);
            }}
          >
            show info
          </ButtonLink>
        </Group>
        {showRepositoryOrigin && (
          <Callout style={{marginTop: 10}}>
            <RepositoryOriginInformation origin={repositoryOrigin} />
          </Callout>
        )}
      </td>
      <td></td>
      <td>
        {latestTick ? (
          <TickTag tick={latestTick} jobType={JobType.SENSOR} />
        ) : (
          <span style={{color: Colors.GRAY4}}>None</span>
        )}
      </td>
      <td>
        <div style={{display: 'flex'}}>
          {runs.length ? (
            runs.map((run) => {
              return (
                <div
                  style={{
                    cursor: 'pointer',
                    marginRight: '4px',
                  }}
                  key={run.runId}
                >
                  <Link to={`/instance/runs/${run.runId}`}>
                    <Tooltip
                      position={'top'}
                      content={titleForRun(run)}
                      wrapperTagName="div"
                      targetTagName="div"
                    >
                      <RunStatus status={run.status} />
                    </Tooltip>
                  </Link>
                </div>
              );
            })
          ) : (
            <span style={{color: Colors.GRAY4}}>None</span>
          )}
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
  const {
    id,
    name,
    ticks,
    status,
    repositoryOrigin,
    runs,
    runsCount,
    jobSpecificData,
  } = scheduleState;
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
        <Group direction="horizontal" spacing={8} alignItems="center">
          <div>{name}</div>
          <ButtonLink
            onClick={() => {
              setShowRepositoryOrigin(!showRepositoryOrigin);
            }}
          >
            show info
          </ButtonLink>
        </Group>
        {showRepositoryOrigin && (
          <Callout style={{marginTop: 10}}>
            <RepositoryOriginInformation origin={repositoryOrigin} />
          </Callout>
        )}
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
            <div>-</div>
          )}
        </div>
      </td>
      <td>{latestTick ? <TickTag tick={latestTick} jobType={JobType.SCHEDULE} /> : null}</td>
      <td>
        <div style={{display: 'flex'}}>
          {runs.map((run) => {
            return (
              <div
                style={{
                  cursor: 'pointer',
                  marginRight: '4px',
                }}
                key={run.runId}
              >
                <Link to={`/instance/runs/${run.runId}`}>
                  <Tooltip
                    position={'top'}
                    content={titleForRun(run)}
                    wrapperTagName="div"
                    targetTagName="div"
                  >
                    <RunStatus status={run.status} />
                  </Tooltip>
                </Link>
              </div>
            );
          })}
          {runsCount > NUM_RUNS_TO_DISPLAY && (
            <Link
              to={`/instance/runs/?q=${encodeURIComponent(`tag:dagster/schedule_name=${name}`)}`}
              style={{verticalAlign: 'top'}}
            >
              {' '}
              +{runsCount - NUM_RUNS_TO_DISPLAY} more
            </Link>
          )}
        </div>
      </td>
    </tr>
  );
};
