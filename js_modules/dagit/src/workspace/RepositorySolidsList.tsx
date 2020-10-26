import {gql, useQuery} from '@apollo/client';
import {Colors, NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Table} from 'src/ui/Table';
import {RepositorySolidsListQuery} from 'src/workspace/types/RepositorySolidsListQuery';
import {workspacePath} from 'src/workspace/workspacePath';

const REPOSITORY_SOLIDS_LIST_QUERY = gql`
  query RepositorySolidsListQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on Repository {
        id
        usedSolids {
          definition {
            description
            name
          }
          invocations {
            pipeline {
              name
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

export const RepositorySolidsList = (props: RepositoryViewProps) => {
  const {repoName, repoLocation} = props;
  const repositorySelector = {
    repositoryName: repoName,
    repositoryLocationName: repoLocation,
  };

  const {data, error, loading} = useQuery<RepositorySolidsListQuery>(REPOSITORY_SOLIDS_LIST_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {repositorySelector},
  });

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

  const {usedSolids} = data?.repositoryOrError;

  return (
    <Table striped style={{width: '100%'}}>
      <thead>
        <tr>
          <th>Solid name</th>
          <th>Pipelines</th>
        </tr>
      </thead>
      <tbody>
        {usedSolids.map((solid) => {
          const {
            definition: {description, name: solidName},
            invocations,
          } = solid;
          const pipelines = new Set(invocations.map((invocation) => invocation.pipeline.name));

          return (
            <tr key={`${solidName}`}>
              <td style={{width: '40%'}}>
                <div>
                  <Link to={workspacePath(repoName, repoLocation, `/solids/${solidName}`)}>
                    {solidName}
                  </Link>
                </div>
                <span style={{fontSize: '12px', color: Colors.GRAY3}}>{description}</span>
              </td>
              <td>
                {pipelines.size ? (
                  Array.from(pipelines).map((pipeline) => (
                    <div key={pipeline}>
                      <Link to={workspacePath(repoName, repoLocation, `/pipelines/${pipeline}`)}>
                        {pipeline}
                      </Link>
                    </div>
                  ))
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
