import {gql, useQuery} from '@apollo/client';
import {Colors, NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {RunStatusWithStats} from 'src/runs/RunStatusDots';
import {Table} from 'src/ui/Table';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {RepositoryPipelinesListQuery} from 'src/workspace/types/RepositoryPipelinesListQuery';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

const REPOSITORY_PIPELINES_LIST_QUERY = gql`
  query RepositoryPipelinesListQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on Repository {
        id
        pipelines {
          name
          description
          runs {
            runId
            status
          }
        }
      }
      ... on RepositoryNotFoundError {
        message
      }
    }
  }
`;

interface Props {
  repoAddress: RepoAddress;
}

export const RepositoryPipelinesList: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const {data, error, loading} = useQuery<RepositoryPipelinesListQuery>(
    REPOSITORY_PIPELINES_LIST_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      variables: {repositorySelector},
    },
  );

  if (loading) {
    return null;
  }

  if (error || !data || data?.repositoryOrError?.__typename !== 'Repository') {
    debugger;
    return (
      <NonIdealState
        title="Unable to load pipelines"
        description={`Could not load pipelines for ${repoAddressAsString(repoAddress)}`}
      />
    );
  }

  const {pipelines} = data?.repositoryOrError;

  return (
    <Table striped style={{width: '100%'}}>
      <thead>
        <tr>
          <th>Pipeline name</th>
          <th>Recent runs</th>
        </tr>
      </thead>
      <tbody>
        {pipelines.map((pipeline) => {
          const {name, runs} = pipeline;
          return (
            <tr key={name}>
              <td style={{width: '60%'}}>
                <div>
                  <Link to={workspacePathFromAddress(repoAddress, `/pipelines/${name}`)}>
                    {name}
                  </Link>
                </div>
                <span style={{fontSize: '12px', color: Colors.GRAY3}}>{pipeline.description}</span>
              </td>
              <td>
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
              </td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
};
