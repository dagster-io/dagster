import {Box, MiddleTruncate, useDelayedState} from '@dagster-io/ui-components';
import {forwardRef, useMemo} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {SINGLE_JOB_QUERY} from './SingleJobQuery';
import {CaptionText, LoadingOrNone} from './VirtualizedWorkspaceTable';
import {buildPipelineSelector} from './WorkspaceContext/util';
import {RepoAddress} from './types';
import {SingleJobQuery, SingleJobQueryVariables} from './types/SingleJobQuery.types';
import {workspacePathFromAddress} from './workspacePath';
import {useQuery} from '../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {JobMenu} from '../instance/JobMenu';
import {LastRunSummary} from '../instance/LastRunSummary';
import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {RunStatusPezList} from '../runs/RunStatusPez';
import {HeaderCell, HeaderRow, RowCell} from '../ui/VirtualizedTable';

const TEMPLATE_COLUMNS = '1.5fr 1fr 180px 96px 80px';

interface JobRowProps {
  name: string;
  index: number;
  isJob: boolean;
  repoAddress: RepoAddress;
}

export const VirtualizedJobRow = forwardRef(
  (props: JobRowProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {name, isJob, repoAddress, index} = props;

    // Wait 100ms before querying in case we're scrolling the table really fast
    const shouldQuery = useDelayedState(100);
    const queryResult = useQuery<SingleJobQuery, SingleJobQueryVariables>(SINGLE_JOB_QUERY, {
      variables: {
        selector: buildPipelineSelector(repoAddress, name),
      },
      skip: !shouldQuery,
    });
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
      <div data-index={index} ref={ref}>
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
      </div>
    );
  },
);

export const VirtualizedJobHeader = () => {
  return (
    <HeaderRow templateColumns={TEMPLATE_COLUMNS} sticky>
      <HeaderCell>名称</HeaderCell>
      <HeaderCell>定时任务/监控器</HeaderCell>
      <HeaderCell>最新运行</HeaderCell>
      <HeaderCell>运行历史</HeaderCell>
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
