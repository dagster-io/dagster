import {Box, MiddleTruncate, useDelayedState} from '@dagster-io/ui-components';
import {forwardRef, useMemo} from 'react';
import {Link} from 'react-router-dom';

import {SINGLE_JOB_QUERY} from './SingleJobQuery';
import {CaptionText, LoadingOrNone} from './VirtualizedWorkspaceTable';
import {buildPipelineSelector} from './WorkspaceContext/util';
import styles from './css/VirtualizedJobRow.module.css';
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
        <Box border="bottom" className={styles.rowGrid}>
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
                <div className={styles.scheduleSensorTagContainer}>
                  <ScheduleOrSensorTag
                    schedules={schedules}
                    sensors={sensors}
                    repoAddress={repoAddress}
                  />
                </div>
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
        </Box>
      </div>
    );
  },
);

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
