import {gql, useQuery} from '@apollo/client';
import {
  Box,
  ButtonWIP,
  ButtonLink,
  ColorsWIP,
  DialogFooter,
  DialogWIP,
  StyledTable,
  Table,
  TagWIP,
  Subheading,
  Tooltip,
  FontFamily,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {timingStringForStatus} from '../runs/RunDetails';
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {RunTime, RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {ScheduleSwitch, SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {humanCronString} from '../schedules/humanCronString';
import {ScheduleSwitchFragment} from '../schedules/types/ScheduleSwitchFragment';
import {SensorSwitch, SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {SensorSwitchFragment} from '../sensors/types/SensorSwitchFragment';
import {RunStatus} from '../types/globalTypes';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {JobMetadataFragment as Job} from './types/JobMetadataFragment';
import {JobMetadataQuery} from './types/JobMetadataQuery';
import {RunMetadataFragment} from './types/RunMetadataFragment';

interface Props {
  pipelineName: string;
  repoAddress: RepoAddress;
}

export const JobMetadata: React.FC<Props> = (props) => {
  const {pipelineName, repoAddress} = props;

  const {data} = useQuery<JobMetadataQuery>(JOB_METADATA_QUERY, {
    variables: {
      params: {
        pipelineName,
        repositoryName: repoAddress.name,
        repositoryLocationName: repoAddress.location,
      },
      runsFilter: {
        pipelineName,
      },
    },
  });

  const job = React.useMemo(() => {
    if (data?.pipelineOrError && data.pipelineOrError.__typename === 'Pipeline') {
      return data.pipelineOrError;
    }
    return null;
  }, [data]);

  const runs = React.useMemo(() => {
    if (data?.pipelineRunsOrError && data.pipelineRunsOrError.__typename === 'Runs') {
      return data.pipelineRunsOrError.results;
    }
    return [];
  }, [data]);

  const lastRun = runs[0] || null;

  return (
    <>
      {job ? <JobScheduleOrSensorTag job={job} repoAddress={repoAddress} /> : null}
      {lastRun ? <LatestRunTag run={lastRun} /> : null}
      {runs.length ? <RelatedAssetsTag runs={runs} /> : null}
    </>
  );
};

const JobScheduleOrSensorTag: React.FC<{job: Job; repoAddress: RepoAddress}> = ({
  job,
  repoAddress,
}) => {
  const matchingSchedules = React.useMemo(() => {
    if (job?.__typename === 'Pipeline' && job.schedules.length) {
      return job.schedules;
    }
    return [];
  }, [job]);

  const matchingSensors = React.useMemo(() => {
    if (job?.__typename === 'Pipeline' && job.sensors.length) {
      return job.sensors;
    }
    return [];
  }, [job]);

  return (
    <ScheduleOrSensorTag
      schedules={matchingSchedules}
      sensors={matchingSensors}
      repoAddress={repoAddress}
    />
  );
};

export const ScheduleOrSensorTag: React.FC<{
  schedules: ScheduleSwitchFragment[];
  sensors: SensorSwitchFragment[];
  repoAddress: RepoAddress;
}> = ({schedules, sensors, repoAddress}) => {
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

    const dialogTitle =
      scheduleCount && sensorCount
        ? 'Schedules and sensors'
        : scheduleCount
        ? 'Schedules'
        : 'Sensors';

    const icon = scheduleCount > 1 ? 'schedule' : 'sensors';

    return (
      <>
        <TagWIP icon={icon}>
          <ButtonLink onClick={() => setOpen(true)} color={ColorsWIP.Link}>
            {buttonText}
          </ButtonLink>
        </TagWIP>
        <DialogWIP
          title={dialogTitle}
          canOutsideClickClose
          canEscapeKeyClose
          isOpen={open}
          style={{width: '50vw', minWidth: '600px', maxWidth: '800px'}}
          onClose={() => setOpen(false)}
        >
          <Box padding={{bottom: 12}}>
            {schedules.length ? (
              <>
                {sensors.length ? (
                  <Box padding={{vertical: 16, horizontal: 24}}>
                    <Subheading>Schedules ({schedules.length})</Subheading>
                  </Box>
                ) : null}
                <Table>
                  <thead>
                    <tr>
                      <th style={{width: '80px'}} />
                      <th>Schedule name</th>
                      <th>Schedule</th>
                    </tr>
                  </thead>
                  <tbody>
                    {schedules.map((schedule) => (
                      <tr key={schedule.name}>
                        <td>
                          <ScheduleSwitch repoAddress={repoAddress} schedule={schedule} />
                        </td>
                        <td>
                          <Link
                            to={workspacePathFromAddress(
                              repoAddress,
                              `/schedules/${schedule.name}`,
                            )}
                          >
                            {schedule.name}
                          </Link>
                        </td>
                        <td>{humanCronString(schedule.cronSchedule)}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </>
            ) : null}
            {sensors.length ? (
              <>
                {schedules.length ? (
                  <Box padding={{vertical: 16, horizontal: 24}}>
                    <Subheading>Sensors ({sensors.length})</Subheading>
                  </Box>
                ) : null}
                <Table>
                  <thead>
                    <tr>
                      <th style={{width: '80px'}} />
                      <th>Sensor name</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sensors.map((sensor) => (
                      <tr key={sensor.name}>
                        <td>
                          <SensorSwitch repoAddress={repoAddress} sensor={sensor} />
                        </td>
                        <td>
                          <Link
                            to={workspacePathFromAddress(repoAddress, `/sensors/${sensor.name}`)}
                          >
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
            <ButtonWIP intent="primary" onClick={() => setOpen(false)}>
              OK
            </ButtonWIP>
          </DialogFooter>
        </DialogWIP>
      </>
    );
  }

  if (scheduleCount) {
    return <MatchingSchedule schedule={schedules[0]} repoAddress={repoAddress} />;
  }

  if (sensorCount) {
    return <MatchingSensor sensor={sensors[0]} repoAddress={repoAddress} />;
  }

  return null;
};

const MatchingSchedule: React.FC<{schedule: ScheduleSwitchFragment; repoAddress: RepoAddress}> = ({
  schedule,
  repoAddress,
}) => {
  const running = schedule.scheduleState.status === 'RUNNING';
  const tag = (
    <TagWIP intent={running ? 'primary' : 'none'} icon="schedule">
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        Schedule:
        <Link to={workspacePathFromAddress(repoAddress, `/schedules/${schedule.name}`)}>
          {humanCronString(schedule.cronSchedule)}
        </Link>
        <ScheduleSwitch size="small" repoAddress={repoAddress} schedule={schedule} />
      </Box>
    </TagWIP>
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

const MatchingSensor: React.FC<{sensor: SensorSwitchFragment; repoAddress: RepoAddress}> = ({
  sensor,
  repoAddress,
}) => {
  const running = sensor.sensorState.status === 'RUNNING';
  return (
    <TagWIP intent={running ? 'primary' : 'none'} icon="sensors">
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        Sensor:
        <Link to={workspacePathFromAddress(repoAddress, `/sensors/${sensor.name}`)}>
          {sensor.name}
        </Link>
        <SensorSwitch size="small" repoAddress={repoAddress} sensor={sensor} />
      </Box>
    </TagWIP>
  );
};

const TIME_FORMAT = {showSeconds: true, showTimezone: false};

export const LatestRunTag: React.FC<{run: RunMetadataFragment}> = ({run}) => {
  const stats = React.useMemo(() => {
    return {start: run.startTime, end: run.endTime, status: run.status};
  }, [run]);

  const intent = () => {
    switch (run.status) {
      case RunStatus.SUCCESS:
        return 'success';
      case RunStatus.CANCELED:
      case RunStatus.CANCELING:
      case RunStatus.FAILURE:
        return 'danger';
      default:
        return 'none';
    }
  };

  return (
    <TagWIP intent={intent()}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        <RunStatusIndicator status={run.status} size={10} />
        Latest run:
        {stats ? (
          <Tooltip
            placement="bottom"
            content={
              <StyledTable>
                <tbody>
                  <tr>
                    <td style={{color: ColorsWIP.Gray300}}>
                      <Box padding={{right: 16}}>Started</Box>
                    </td>
                    <td>
                      {stats.start ? (
                        <TimestampDisplay timestamp={stats.start} timeFormat={TIME_FORMAT} />
                      ) : (
                        timingStringForStatus(stats.status)
                      )}
                    </td>
                  </tr>
                  <tr>
                    <td style={{color: ColorsWIP.Gray300}}>Ended</td>
                    <td>
                      {stats.end ? (
                        <TimestampDisplay timestamp={stats.end} timeFormat={TIME_FORMAT} />
                      ) : (
                        timingStringForStatus(stats.status)
                      )}
                    </td>
                  </tr>
                </tbody>
              </StyledTable>
            }
          >
            <Link to={`/instance/runs/${run.id}`}>
              <RunTime run={run} />
            </Link>
          </Tooltip>
        ) : null}
      </Box>
    </TagWIP>
  );
};

const RelatedAssetsTag: React.FC<{runs: RunMetadataFragment[]}> = ({runs}) => {
  const [open, setOpen] = React.useState(false);

  const assetMap = {};
  runs.forEach((run) => {
    run.assets.forEach((asset) => {
      const assetKeyStr = asset.key.path.join('/');
      assetMap[assetKeyStr] = true;
    });
  });

  const keys = Object.keys(assetMap);
  if (keys.length === 0) {
    return null;
  }

  if (keys.length === 1) {
    const key = keys[0];
    return (
      <TagWIP icon="asset">
        Asset: <Link to={`/instance/assets/${key}`}>{key}</Link>
      </TagWIP>
    );
  }

  return (
    <>
      <TagWIP icon="asset">
        <ButtonLink
          color={ColorsWIP.Link}
          onClick={() => setOpen(true)}
        >{`View ${keys.length} assets`}</ButtonLink>
      </TagWIP>
      <DialogWIP
        title="Related assets"
        canOutsideClickClose
        canEscapeKeyClose
        isOpen={open}
        onClose={() => setOpen(false)}
        style={{maxWidth: '80%', minWidth: '500px', width: 'auto'}}
      >
        <Box padding={{bottom: 12}}>
          <Table>
            <tbody>
              {keys.map((key) => (
                <tr key={key}>
                  <td>
                    <Link
                      key={key}
                      to={`/instance/assets/${key}`}
                      style={{wordBreak: 'break-word'}}
                    >
                      {key}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Box>
        <DialogFooter>
          <ButtonWIP intent="primary" onClick={() => setOpen(false)}>
            OK
          </ButtonWIP>
        </DialogFooter>
      </DialogWIP>
    </>
  );
};

export const RUN_METADATA_FRAGMENT = gql`
  fragment RunMetadataFragment on PipelineRun {
    id
    status
    assets {
      id
      key {
        path
      }
    }
    ...RunTimeFragment
  }
  ${RUN_TIME_FRAGMENT}
`;

export const JOB_METADATA_FRAGMENT = gql`
  fragment JobMetadataFragment on Pipeline {
    id
    isJob
    name
    schedules {
      id
      mode
      ...ScheduleSwitchFragment
    }
    sensors {
      id
      targets {
        pipelineName
        mode
      }
      ...SensorSwitchFragment
    }
  }
  ${SCHEDULE_SWITCH_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
`;

const JOB_METADATA_QUERY = gql`
  query JobMetadataQuery($params: PipelineSelector!, $runsFilter: RunsFilter) {
    pipelineOrError(params: $params) {
      ... on Pipeline {
        id
        ...JobMetadataFragment
      }
    }
    pipelineRunsOrError(filter: $runsFilter, limit: 5) {
      ... on PipelineRuns {
        results {
          id
          ...RunMetadataFragment
        }
      }
    }
  }
  ${JOB_METADATA_FRAGMENT}
  ${RUN_METADATA_FRAGMENT}
`;
