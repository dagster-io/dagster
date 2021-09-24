import {gql, useQuery} from '@apollo/client';
import {Button, Classes, Colors, Dialog} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';
import {timingStringForStatus} from '../runs/RunDetails';
import {RunStatus} from '../runs/RunStatusDots';
import {RunTime, RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {ScheduleSwitch, SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {SensorSwitch, SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {MetadataTable, StyledTable} from '../ui/MetadataTable';
import {Mono} from '../ui/Text';
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

  const {data, loading} = useQuery<JobMetadataQuery>(JOB_METADATA_QUERY, {
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
    <MetadataTable
      spacing={2}
      rows={[
        {
          key: 'Schedule/sensor',
          value: job ? (
            <ScheduleOrSensor job={job} mode={pipelineMode} repoAddress={repoAddress} />
          ) : (
            <GrayText>{loading ? 'Loading…' : 'None'}</GrayText>
          ),
        },
        {
          key: 'Latest run',
          value: lastRun ? (
            <LatestRun run={lastRun} />
          ) : (
            <GrayText>{loading ? 'Loading…' : 'None'}</GrayText>
          ),
        },
        {
          key: 'Related assets',
          value: runs.length ? (
            <RelatedAssets runs={runs} />
          ) : (
            <GrayText>{loading ? 'Loading…' : 'None'}</GrayText>
          ),
        },
      ]}
    />
  );
};

const ScheduleOrSensor: React.FC<{job: Job; mode: string; repoAddress: RepoAddress}> = ({
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

    return (
      <>
        <ButtonLink onClick={() => setOpen(true)}>{buttonText}</ButtonLink>
        <Dialog
          title={dialogTitle}
          canOutsideClickClose
          canEscapeKeyClose
          isOpen={open}
          onClose={() => setOpen(false)}
        >
          <div className={Classes.DIALOG_BODY}>
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
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button text="OK" onClick={() => setOpen(false)} />
            </div>
          </div>
        </Dialog>
      </>
    );
  }

  if (scheduleCount) {
    return <MatchingSchedule schedule={matchingSchedules[0]} repoAddress={repoAddress} />;
  }

  if (sensorCount) {
    return <MatchingSensor sensor={matchingSensors[0]} repoAddress={repoAddress} />;
  }

  return <GrayText>None</GrayText>;
};

const MatchingSchedule: React.FC<{schedule: Schedule; repoAddress: RepoAddress}> = ({
  schedule,
  repoAddress,
}) => (
  <Group direction="row" spacing={8} alignItems="center">
    <IconWIP name="schedule" color={ColorsWIP.Gray700} />
    <Link to={workspacePathFromAddress(repoAddress, `/schedules/${schedule.name}`)}>
      {schedule.name}
    </Link>
    <ScheduleSwitch large={false} repoAddress={repoAddress} schedule={schedule} />
  </Group>
);

const MatchingSensor: React.FC<{sensor: Sensor; repoAddress: RepoAddress}> = ({
  sensor,
  repoAddress,
}) => (
  <Group direction="row" spacing={8} alignItems="center">
    <IconWIP name="sensors" color={ColorsWIP.Gray700} />
    <Link to={workspacePathFromAddress(repoAddress, `/sensors/${sensor.name}`)}>{sensor.name}</Link>
    <SensorSwitch large={false} repoAddress={repoAddress} sensor={sensor} />
  </Group>
);

const TIME_FORMAT = {showSeconds: true, showTimezone: false};

const LatestRun: React.FC<{run: RunMetadataFragment}> = ({run}) => {
  const stats = React.useMemo(() => {
    if (run.stats.__typename === 'PipelineRunStatsSnapshot') {
      return {start: run.stats.startTime, end: run.stats.endTime, status: run.status};
    }
    return null;
  }, [run]);

  return (
    <Group direction="row" spacing={8} alignItems="baseline">
      <RunStatus status={run.status} size={10} />
      <Mono>
        <Link to={`/instance/runs/${run.id}`}>{run.id.slice(0, 8)}</Link>
      </Mono>
      {stats ? (
        <Tooltip
          placement="bottom"
          content={
            <StyledTable>
              <tbody>
                <tr>
                  <td style={{color: Colors.GRAY4}}>
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
                  <td style={{color: Colors.GRAY4}}>Ended</td>
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
          <RunTime run={run} />
        </Tooltip>
      ) : null}
    </Group>
  );
};

const RelatedAssets: React.FC<{runs: RunMetadataFragment[]}> = ({runs}) => {
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
    return <GrayText>None</GrayText>;
  }

  if (keys.length === 1) {
    const key = keys[0];
    return <Link to={`/instance/assets/${key}`}>{key}</Link>;
  }

  return (
    <>
      <ButtonLink onClick={() => setOpen(true)}>{`View ${keys.length} assets`}</ButtonLink>
      <Dialog
        title="Related assets"
        canOutsideClickClose
        canEscapeKeyClose
        isOpen={open}
        onClose={() => setOpen(false)}
        style={{maxWidth: '80%', minWidth: '500px', width: 'auto'}}
      >
        <div className={Classes.DIALOG_BODY}>
          <Group direction="column" spacing={16}>
            {keys.map((key) => (
              <Link key={key} to={`/instance/assets/${key}`} style={{wordBreak: 'break-word'}}>
                {key}
              </Link>
            ))}
          </Group>
        </div>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button text="OK" onClick={() => setOpen(false)} />
          </div>
        </div>
      </Dialog>
    </>
  );
};

const GrayText = styled.div`
  color: ${Colors.GRAY3};
`;

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
