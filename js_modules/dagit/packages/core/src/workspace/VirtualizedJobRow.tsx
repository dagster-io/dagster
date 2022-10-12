import {gql, useLazyQuery} from '@apollo/client';
import {Box, Caption, Colors, MiddleTruncate} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';
import {JobMenu} from '../instance/JobMenu';
import {LastRunSummary} from '../instance/LastRunSummary';
import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {RunStatusPezList} from '../runs/RunStatusPez';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {Row, RowCell} from '../ui/VirtualizedTable';

import {LoadingOrNone, useDelayedRowQuery} from './VirtualizedWorkspaceTable';
import {buildPipelineSelector} from './WorkspaceContext';
import {RepoAddress} from './types';
import {SingleJobQuery, SingleJobQueryVariables} from './types/SingleJobQuery';
import {workspacePathFromAddress} from './workspacePath';

interface JobRowProps {
  name: string;
  isJob: boolean;
  repoAddress: RepoAddress;
  height: number;
  start: number;
}

export const VirtualizedJobRow = (props: JobRowProps) => {
  const {name, isJob, repoAddress, start, height} = props;

  const [queryJob, queryResult] = useLazyQuery<SingleJobQuery, SingleJobQueryVariables>(
    SINGLE_JOB_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      variables: {
        selector: buildPipelineSelector(repoAddress, name),
      },
    },
  );

  useDelayedRowQuery(queryJob);
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const {data} = queryResult;

  const {schedules, sensors} = React.useMemo(() => {
    if (data?.pipelineOrError.__typename === 'Pipeline') {
      const {schedules, sensors} = data.pipelineOrError;
      return {schedules, sensors};
    }
    return {schedules: [], sensors: []};
  }, [data]);

  const latestRuns = React.useMemo(() => {
    if (data?.pipelineOrError.__typename === 'Pipeline') {
      const runs = data.pipelineOrError.runs;
      if (runs.length) {
        return [...runs];
      }
    }
    return [];
  }, [data]);

  return (
    <Row $height={height} $start={start}>
      <RowGrid border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}>
        <RowCell>
          <div style={{whiteSpace: 'nowrap', fontWeight: 500}}>
            <Link to={workspacePathFromAddress(repoAddress, `/jobs/${name}`)}>
              <MiddleTruncate text={name} />
            </Link>
          </div>
          <div
            style={{
              maxWidth: '100%',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            <Caption
              style={{
                color: Colors.Gray500,
                whiteSpace: 'nowrap',
              }}
            >
              {data?.pipelineOrError.__typename === 'Pipeline'
                ? data.pipelineOrError.description
                : ''}
            </Caption>
          </div>
        </RowCell>
        <RowCell>
          {schedules.length || sensors.length ? (
            <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 8}}>
              <ScheduleOrSensorTag
                schedules={schedules}
                sensors={sensors}
                repoAddress={repoAddress}
              />
              {/* {schedules.length ? <NextTick schedules={schedules} /> : null} */}
            </Box>
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          {latestRuns.length ? (
            <LastRunSummary run={latestRuns[0]} showButton={false} showHover name={name} />
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          {latestRuns.length ? (
            <RunStatusPezList jobName={name} runs={[...latestRuns].reverse()} fade />
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          <div>
            <JobMenu job={{isJob, name, runs: latestRuns}} repoAddress={repoAddress} />
          </div>
        </RowCell>
      </RowGrid>
    </Row>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: 34% 30% 20% 8% 8%;
  height: 100%;
`;

const SINGLE_JOB_QUERY = gql`
  query SingleJobQuery($selector: PipelineSelector!) {
    pipelineOrError(params: $selector) {
      ... on Pipeline {
        id
        name
        isJob
        description
        runs(limit: 5) {
          id
          ...RunTimeFragment
        }
        schedules {
          id
          ...ScheduleSwitchFragment
        }
        sensors {
          id
          ...SensorSwitchFragment
        }
      }
    }
  }

  ${RUN_TIME_FRAGMENT}
  ${SCHEDULE_SWITCH_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
`;
