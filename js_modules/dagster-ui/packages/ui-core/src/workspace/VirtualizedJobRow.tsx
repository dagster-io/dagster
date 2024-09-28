import {Box, MiddleTruncate} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {CaptionText, LoadingOrNone, useDelayedRowQuery} from './VirtualizedWorkspaceTable';
import {buildPipelineSelector} from './WorkspaceContext/util';
import {RepoAddress} from './types';
import {SingleJobQuery, SingleJobQueryVariables} from './types/VirtualizedJobRow.types';
import {workspacePathFromAddress} from './workspacePath';
import {gql, useLazyQuery} from '../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {JobMenu} from '../instance/JobMenu';
import {LastRunSummary} from '../instance/LastRunSummary';
import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {RunStatusPezList} from '../runs/RunStatusPez';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {HeaderCell, HeaderRow, Row, RowCell} from '../ui/VirtualizedTable';

const TEMPLATE_COLUMNS = '1.5fr 1fr 180px 96px 80px';

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
      variables: {
        selector: buildPipelineSelector(repoAddress, name),
      },
    },
  );
  useDelayedRowQuery(queryJob);
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const {data} = queryResult;
  const pipeline =
    data?.pipelineOrError.__typename === 'Pipeline' ? data?.pipelineOrError : undefined;

  const {schedules, sensors} = useMemo(() => {
    if (pipeline) {
      const {schedules, sensors} = pipeline;
      return {schedules, sensors};
    }
    return {schedules: [], sensors: []};
  }, [pipeline]);

  const latestRuns = useMemo(() => {
    if (pipeline) {
      const {runs} = pipeline;
      if (runs.length) {
        return [...runs];
      }
    }
    return [];
  }, [pipeline]);

  return (
    <Row $height={height} $start={start}>
      <RowGrid border="bottom">
        <RowCell>
          <div style={{maxWidth: '100%', whiteSpace: 'nowrap', fontWeight: 500}}>
            <Link to={workspacePathFromAddress(repoAddress, `/jobs/${name}`)}>
              <MiddleTruncate text={name} />
            </Link>
          </div>
          <CaptionText>{pipeline?.description || ''}</CaptionText>
        </RowCell>
        <RowCell>
          {schedules.length || sensors.length ? (
            <Box flex={{direction: 'column', alignItems: 'flex-start', gap: 8}}>
              <ScheduleSensorTagContainer>
                <ScheduleOrSensorTag
                  schedules={schedules}
                  sensors={sensors}
                  repoAddress={repoAddress}
                />
              </ScheduleSensorTagContainer>
            </Box>
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          {latestRuns[0] ? (
            <LastRunSummary
              run={latestRuns[0]}
              showButton={false}
              showHover
              showSummary={false}
              name={name}
            />
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          {latestRuns.length ? (
            <Box padding={{top: 4}}>
              <RunStatusPezList jobName={name} runs={[...latestRuns].reverse()} fade />
            </Box>
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          <Box flex={{justifyContent: 'flex-end'}} style={{marginTop: '-2px'}}>
            <JobMenu
              job={{name, isJob, runs: latestRuns}}
              isAssetJob={pipeline ? pipeline.isAssetJob : 'loading'}
              repoAddress={repoAddress}
            />
          </Box>
        </RowCell>
      </RowGrid>
    </Row>
  );
};

export const VirtualizedJobHeader = () => {
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>Name</HeaderCell>
      <HeaderCell>Schedules/sensors</HeaderCell>
      <HeaderCell>Latest run</HeaderCell>
      <HeaderCell>Run history</HeaderCell>
      <HeaderCell></HeaderCell>
    </HeaderRow>
  );
};

const RowGrid = styled(Box)`
  display: grid;
  grid-template-columns: ${TEMPLATE_COLUMNS};
  height: 100%;
`;

const ScheduleSensorTagContainer = styled.div`
  width: 100%;

  > .bp5-popover-target {
    width: 100%;
  }
`;

const SINGLE_JOB_QUERY = gql`
  query SingleJobQuery($selector: PipelineSelector!) {
    pipelineOrError(params: $selector) {
      ... on Pipeline {
        id
        name
        isJob
        isAssetJob
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
