import {Tooltip, Colors, NonIdealState} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {Link} from 'react-router-dom';

import {RunStatusWithStats} from 'src/runs/RunStatusDots';
import {humanCronString} from 'src/schedules/humanCronString';
import {Table} from 'src/ui/Table';
import {RepositorySchedulesListQuery} from 'src/workspace/types/RepositorySchedulesListQuery';
import {workspacePath} from 'src/workspace/workspacePath';

const REPOSITORY_SCHEDULES_LIST_QUERY = gql`
  query RepositorySchedulesListQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on Repository {
        id
        pipelines {
          name
          schedules {
            cronSchedule
            mode
            name
            pipelineName
            scheduleState {
              status
              runs {
                runId
                status
              }
            }
          }
        }
      }
      ... on RepositoryNotFoundError {
        message
      }
    }
  }
`;

interface RepositoryViewProps {
  repoName: string;
  repoLocation: string;
}

export const RepositorySchedulesList = (props: RepositoryViewProps) => {
  const {repoName, repoLocation} = props;
  const repositorySelector = {
    repositoryName: repoName,
    repositoryLocationName: repoLocation,
  };

  const {data, error, loading} = useQuery<RepositorySchedulesListQuery>(
    REPOSITORY_SCHEDULES_LIST_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      variables: {repositorySelector},
    },
  );

  if (loading) {
    return null;
  }

  if (error || !data || data?.repositoryOrError?.__typename !== 'Repository') {
    return (
      <NonIdealState
        title="Unable to load pipelines"
        description={`Could not load pipelines for ${repoName}@${repoLocation}`}
      />
    );
  }

  const {pipelines} = data?.repositoryOrError;
  const pipelinesWithSchedules = pipelines.filter((pipeline) => !!pipeline.schedules.length);
  const schedules = pipelinesWithSchedules
    .reduce((accum, pipeline) => [...accum, ...pipeline.schedules], [])
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <Table striped style={{width: '100%'}}>
      <thead>
        <tr>
          <th>Schedule name</th>
          <th>Pipeline name</th>
          <th>Schedule</th>
          <th>Mode</th>
          <th>Recent runs</th>
        </tr>
      </thead>
      <tbody>
        {schedules.map((schedule) => {
          const {cronSchedule, mode, name, pipelineName, scheduleState} = schedule;
          const runs = scheduleState?.runs;
          const status = scheduleState?.status;

          return (
            <tr key={`${pipelineName}-${name}`}>
              <td style={{width: '25%'}}>
                <div>
                  <Link to={workspacePath(repoName, repoLocation, `/schedules/${name}`)}>
                    {name}
                  </Link>
                </div>
                {status ? (
                  <span style={{fontSize: '12px', color: Colors.GRAY3}}>{status}</span>
                ) : null}
              </td>
              <td style={{width: '20%'}}>
                <Link to={workspacePath(repoName, repoLocation, `/pipelines/${pipelineName}`)}>
                  {pipelineName}
                </Link>
              </td>
              <td style={{width: '15%'}}>
                {cronSchedule ? (
                  <Tooltip position={'bottom'} content={cronSchedule}>
                    {humanCronString(cronSchedule)}
                  </Tooltip>
                ) : (
                  <div style={{color: Colors.GRAY5}}>-</div>
                )}
              </td>
              <td style={{width: '15%'}}>{`Mode: ${mode}`}</td>
              <td>
                {runs ? (
                  <div style={{display: 'flex', flexDirection: 'row'}}>
                    {runs.map((run) => (
                      <RunStatusWithStats
                        key={run.runId}
                        runId={run.runId}
                        status={run.status}
                        size={16}
                      />
                    ))}
                  </div>
                ) : (
                  <div style={{color: Colors.GRAY5}}>None</div>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
};
