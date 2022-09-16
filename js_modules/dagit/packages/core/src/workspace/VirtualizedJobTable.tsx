import {gql, useLazyQuery} from '@apollo/client';
import {Box, Caption, Colors, Tag, Tooltip} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {JobMenu} from '../instance/JobMenu';
import {LastRunSummary} from '../instance/LastRunSummary';
import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {RunStatusPezList} from '../runs/RunStatusPez';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {Container, Inner, Row, RowCell} from '../ui/VirtualizedTable';
import {findDuplicateRepoNames} from '../ui/findDuplicateRepoNames';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';

import {LoadingOrNone, RepoRow, useDelayedRowQuery} from './VirtualizedWorkspaceTable';
import {buildPipelineSelector} from './WorkspaceContext';
import {repoAddressAsString} from './repoAddressAsString';
import {RepoAddress} from './types';
import {SingleJobQuery, SingleJobQueryVariables} from './types/SingleJobQuery';
import {workspacePathFromAddress} from './workspacePath';

type Repository = {
  repoAddress: RepoAddress;
  jobs: {
    isJob: boolean;
    name: string;
  }[];
};

interface Props {
  repos: Repository[];
}

type RowType =
  | {type: 'header'; repoAddress: RepoAddress; jobCount: number}
  | {type: 'job'; repoAddress: RepoAddress; isJob: boolean; name: string};

const JOBS_EXPANSION_STATE_STORAGE_KEY = 'jobs-virtualized-expansion-state';

export const VirtualizedJobTable: React.FC<Props> = ({repos}) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const {expandedKeys, onToggle} = useRepoExpansionState(JOBS_EXPANSION_STATE_STORAGE_KEY);

  const flattened: RowType[] = React.useMemo(() => {
    const flat: RowType[] = [];
    repos.forEach(({repoAddress, jobs}) => {
      flat.push({type: 'header', repoAddress, jobCount: jobs.length});
      const repoKey = repoAddressAsString(repoAddress);
      if (expandedKeys.includes(repoKey)) {
        jobs.forEach(({isJob, name}) => {
          flat.push({type: 'job', repoAddress, isJob, name});
        });
      }
    });
    return flat;
  }, [repos, expandedKeys]);

  const duplicateRepoNames = findDuplicateRepoNames(repos.map(({repoAddress}) => repoAddress.name));

  const rowVirtualizer = useVirtualizer({
    count: flattened.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (ii: number) => {
      const row = flattened[ii];
      return row?.type === 'header' ? 32 : 64;
    },
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <Container ref={parentRef}>
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const row: RowType = flattened[index];
          const type = row!.type;
          return type === 'header' ? (
            <RepoRow
              repoAddress={row.repoAddress}
              key={key}
              height={size}
              start={start}
              onToggle={onToggle}
              showLocation={duplicateRepoNames.has(row.repoAddress.name)}
              rightElement={
                <Tooltip
                  content={row.jobCount === 1 ? '1 job' : `${row.jobCount} jobs`}
                  placement="top"
                >
                  <Tag intent="primary">{row.jobCount}</Tag>
                </Tooltip>
              }
            />
          ) : (
            <JobRow
              key={key}
              name={row.name}
              isJob={row.isJob}
              repoAddress={row.repoAddress}
              height={size}
              start={start}
            />
          );
        })}
      </Inner>
    </Container>
  );
};

interface JobRowProps {
  name: string;
  isJob: boolean;
  repoAddress: RepoAddress;
  height: number;
  start: number;
}

const JobRow = (props: JobRowProps) => {
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
          <div style={{whiteSpace: 'nowrap'}}>
            <Link to={workspacePathFromAddress(repoAddress, `/jobs/${name}`)}>{name}</Link>
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
