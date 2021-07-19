import {gql, useQuery} from '@apollo/client';
import {Button, Classes, Colors, Dialog, Icon} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useFeatureFlags} from '../app/Flags';
import {RunStatus} from '../runs/RunStatusDots';
import {TimeElapsed} from '../runs/TimeElapsed';
import {ScheduleSwitch} from '../schedules/ScheduleSwitch';
import {SCHEDULE_FRAGMENT} from '../schedules/ScheduleUtils';
import {SENSOR_FRAGMENT} from '../sensors/SensorFragment';
import {SensorSwitch} from '../sensors/SensorSwitch';
import {ButtonLink} from '../ui/ButtonLink';
import {Group} from '../ui/Group';
import {MetadataTable} from '../ui/MetadataTable';
import {FontFamily} from '../ui/styles';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {
  JobMetadataQuery,
  JobMetadataQuery_pipelineOrError_Pipeline as Job,
  JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results as Run,
  JobMetadataQuery_pipelineOrError_Pipeline_schedules as Schedule,
  JobMetadataQuery_pipelineOrError_Pipeline_sensors as Sensor,
} from './types/JobMetadataQuery';

interface Props {
  pipelineName: string;
  pipelineMode: string;
  repoAddress: RepoAddress;
}

export const JobMetadata: React.FC<Props> = (props) => {
  const {pipelineName, pipelineMode, repoAddress} = props;
  const {data, loading} = useQuery<JobMetadataQuery>(JOB_METADATA_QUERY, {
    variables: {
      params: {
        pipelineName,
        repositoryName: repoAddress.name,
        repositoryLocationName: repoAddress.location,
      },
      runsFilter: {
        pipelineName,
        mode: pipelineMode,
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
        ? job.sensors.filter((sensor) => sensor.mode === mode)
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
  <Group direction="row" spacing={8}>
    <Icon
      icon="time"
      color={Colors.GRAY3}
      iconSize={13}
      style={{position: 'relative', top: '-2px'}}
    />
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
  <Group direction="row" spacing={8}>
    <Icon
      icon="automatic-updates"
      color={Colors.GRAY3}
      iconSize={13}
      style={{position: 'relative', top: '-2px'}}
    />
    <Link to={workspacePathFromAddress(repoAddress, `/sensors/${sensor.name}`)}>{sensor.name}</Link>
    <SensorSwitch large={false} repoAddress={repoAddress} sensor={sensor} />
  </Group>
);

const LatestRun: React.FC<{run: Run}> = ({run}) => {
  const stats = React.useMemo(() => {
    if (run.stats.__typename === 'PipelineRunStatsSnapshot') {
      return {start: run.stats.startTime, end: run.stats.endTime};
    }
    return null;
  }, [run]);

  return (
    <Group direction="row" spacing={8} alignItems="center">
      <RunStatus status={run.status} />
      <div style={{fontFamily: FontFamily.monospace}}>
        <Link to={`/instance/runs/${run.id}`}>{run.id.slice(0, 8)}</Link>
      </div>
      {stats ? <TimeElapsed startUnix={stats.start} endUnix={stats.end} /> : null}
    </Group>
  );
};

const RelatedAssets: React.FC<{runs: Run[]}> = ({runs}) => {
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
      >
        <div className={Classes.DIALOG_BODY}>
          <Group direction="column" spacing={16}>
            {keys.map((key) => (
              <Link key={key} to={`/instance/assets/${key}`}>
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

const JOB_METADATA_QUERY = gql`
  query JobMetadataQuery($params: PipelineSelector!, $runsFilter: PipelineRunsFilter) {
    pipelineOrError(params: $params) {
      ... on Pipeline {
        id
        schedules {
          id
          ...ScheduleFragment
        }
        sensors {
          id
          ...SensorFragment
        }
      }
    }
    pipelineRunsOrError(filter: $runsFilter, limit: 5) {
      ... on PipelineRuns {
        results {
          id
          status
          stats {
            ... on PipelineRunStatsSnapshot {
              id
              startTime
              endTime
            }
          }
          assets {
            id
            key {
              path
            }
          }
        }
      }
    }
  }
  ${SCHEDULE_FRAGMENT}
  ${SENSOR_FRAGMENT}
`;
