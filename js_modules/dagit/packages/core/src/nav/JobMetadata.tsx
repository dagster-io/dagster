import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {timingStringForStatus} from '../runs/RunDetails';
import {RunStatus} from '../runs/RunStatusDots';
import {RunTime, RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {ScheduleSwitch, SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {SensorSwitch, SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {PipelineRunStatus} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {DialogBody, DialogFooter, DialogWIP} from '../ui/Dialog';
import {Group} from '../ui/Group';
import {StyledTable} from '../ui/MetadataTable';
import {TagWIP} from '../ui/TagWIP';
import {Tooltip} from '../ui/Tooltip';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {
  JobMetadataQuery,
  JobMetadataQuery_pipelineOrError_Pipeline as Job,
  JobMetadataQuery_pipelineOrError_Pipeline_schedules as Schedule,
  JobMetadataQuery_pipelineOrError_Pipeline_sensors as Sensor,
} from './types/JobMetadataQuery';
import {RunMetadataFragment} from './types/RunMetadataFragment';

interface Props {
  pipelineName: string;
  pipelineMode: string;
  repoAddress: RepoAddress;
}

export const JobMetadata: React.FC<Props> = (props) => {
  const {pipelineName, pipelineMode, repoAddress} = props;
  const {flagPipelineModeTuples} = useFeatureFlags();

  const {data} = useQuery<JobMetadataQuery>(JOB_METADATA_QUERY, {
    variables: {
      params: {
        pipelineName,
        repositoryName: repoAddress.name,
        repositoryLocationName: repoAddress.location,
      },
      runsFilter: {
        pipelineName,
        mode: flagPipelineModeTuples ? pipelineMode : undefined,
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
    if (data?.pipelineRunsOrError && data.pipelineRunsOrError.__typename === 'PipelineRuns') {
      return data.pipelineRunsOrError.results;
    }
    return [];
  }, [data]);

  const lastRun = runs[0] || null;

  return (
    <>
      {job ? <ScheduleOrSensorTag job={job} mode={pipelineMode} repoAddress={repoAddress} /> : null}
      {lastRun ? <LatestRunTag run={lastRun} /> : null}
      {runs.length ? <RelatedAssetsTag runs={runs} /> : null}
    </>
  );
};

const ScheduleOrSensorTag: React.FC<{job: Job; mode: string; repoAddress: RepoAddress}> = ({
  job,
  mode,
  repoAddress,
}) => {
  const {flagPipelineModeTuples} = useFeatureFlags();
  const [open, setOpen] = React.useState(false);

  const matchingSchedules = React.useMemo(() => {
    if (job?.__typename === 'Pipeline' && job.schedules.length) {
      return flagPipelineModeTuples
        ? job.schedules.filter((schedule) => schedule.mode === mode)
        : job.schedules;
    }
    return [];
  }, [flagPipelineModeTuples, job, mode]);

  const matchingSensors = React.useMemo(() => {
    if (job?.__typename === 'Pipeline' && job.sensors.length) {
      return flagPipelineModeTuples
        ? job.sensors.filter((sensor) =>
            sensor.targets?.some(
              (target) => target.mode === mode && target.pipelineName === job.name,
            ),
          )
        : job.sensors;
    }
    return [];
  }, [flagPipelineModeTuples, job, mode]);

  const scheduleCount = matchingSchedules.length;
  const sensorCount = matchingSensors.length;

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
          onClose={() => setOpen(false)}
        >
          <DialogBody>
            <Group direction="column" spacing={16}>
              {matchingSchedules.map((schedule) => (
                <MatchingSchedule
                  key={schedule.name}
                  schedule={schedule}
                  repoAddress={repoAddress}
                />
              ))}
              {matchingSensors.map((sensor) => (
                <MatchingSensor key={sensor.name} sensor={sensor} repoAddress={repoAddress} />
              ))}
            </Group>
          </DialogBody>
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
    return <MatchingSchedule schedule={matchingSchedules[0]} repoAddress={repoAddress} />;
  }

  if (sensorCount) {
    return <MatchingSensor sensor={matchingSensors[0]} repoAddress={repoAddress} />;
  }

  return null;
};

const MatchingSchedule: React.FC<{schedule: Schedule; repoAddress: RepoAddress}> = ({
  schedule,
  repoAddress,
}) => {
  const running = schedule.scheduleState.status === 'RUNNING';
  return (
    <TagWIP intent={running ? 'primary' : 'none'} icon="schedule">
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        Schedule:
        <Link to={workspacePathFromAddress(repoAddress, `/schedules/${schedule.name}`)}>
          {schedule.name}
        </Link>
        <ScheduleSwitch size="small" repoAddress={repoAddress} schedule={schedule} />
      </Box>
    </TagWIP>
  );
};

const MatchingSensor: React.FC<{sensor: Sensor; repoAddress: RepoAddress}> = ({
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

const LatestRunTag: React.FC<{run: RunMetadataFragment}> = ({run}) => {
  const stats = React.useMemo(() => {
    if (run.stats.__typename === 'PipelineRunStatsSnapshot') {
      return {start: run.stats.startTime, end: run.stats.endTime, status: run.status};
    }
    return null;
  }, [run]);

  const intent = () => {
    switch (run.status) {
      case PipelineRunStatus.SUCCESS:
        return 'success';
      case PipelineRunStatus.CANCELED:
      case PipelineRunStatus.CANCELING:
      case PipelineRunStatus.FAILURE:
        return 'danger';
      default:
        return 'none';
    }
  };

  return (
    <TagWIP intent={intent()}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
        <RunStatus status={run.status} size={10} />
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
        <DialogBody>
          <Group direction="column" spacing={16}>
            {keys.map((key) => (
              <Link key={key} to={`/instance/assets/${key}`} style={{wordBreak: 'break-word'}}>
                {key}
              </Link>
            ))}
          </Group>
        </DialogBody>
        <DialogFooter>
          <ButtonWIP intent="primary" onClick={() => setOpen(false)}>
            OK
          </ButtonWIP>
        </DialogFooter>
      </DialogWIP>
    </>
  );
};

const RUN_METADATA_FRAGMENT = gql`
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

const JOB_METADATA_QUERY = gql`
  query JobMetadataQuery($params: PipelineSelector!, $runsFilter: PipelineRunsFilter) {
    pipelineOrError(params: $params) {
      ... on Pipeline {
        id
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
  ${SCHEDULE_SWITCH_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
  ${RUN_METADATA_FRAGMENT}
`;
