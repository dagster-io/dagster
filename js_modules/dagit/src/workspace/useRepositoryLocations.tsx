import {gql, useQuery} from '@apollo/client';
import React from 'react';

import {RepositoryLocationQuery} from 'src/workspace/types/RepositoryLocationQuery';

const REPOSITORY_LOCATION_QUERY = gql`
  query RepositoryLocationQuery {
    repositoryLocationsOrError {
      __typename
      ... on RepositoryLocationConnection {
        nodes {
          __typename
          ... on RepositoryLocation {
            name
          }
          ... on RepositoryLocationLoadFailure {
            name
            error {
              message
            }
          }
        }
      }
    }
  }
`;

export const useRepositoryLocations = () => {
  const {data, loading, refetch} = useQuery<RepositoryLocationQuery>(REPOSITORY_LOCATION_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  const nodes = React.useMemo(() => {
    return data?.repositoryLocationsOrError.__typename === 'RepositoryLocationConnection'
      ? data?.repositoryLocationsOrError.nodes
      : [];
  }, [data]);

  return {nodes, loading, refetch};
};
