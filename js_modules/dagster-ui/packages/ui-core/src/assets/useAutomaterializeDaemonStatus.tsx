import {useQuery, useMutation, gql} from '@apollo/client';
import * as React from 'react';

import {
  GetAutoMaterializePausedQuery,
  GetAutoMaterializePausedQueryVariables,
  SetAutoMaterializePausedMutation,
  SetAutoMaterializePausedMutationVariables,
} from './types/useAutomaterializeDaemonStatus.types';

export function useAutomaterializeDaemonStatus() {
  const {data, loading, refetch} = useQuery<
    GetAutoMaterializePausedQuery,
    GetAutoMaterializePausedQueryVariables
  >(AUTOMATERIALIZE_PAUSED_QUERY);

  const [setAutoMaterializePaused] = useMutation<
    SetAutoMaterializePausedMutation,
    SetAutoMaterializePausedMutationVariables
  >(SET_AUTOMATERIALIZE_PAUSED_MUTATION, {
    onCompleted: () => {
      refetch();
    },
  });

  const setPaused = React.useCallback(
    (paused: boolean) => {
      setAutoMaterializePaused({variables: {paused}});
    },
    [setAutoMaterializePaused],
  );

  return {
    loading: !data && loading,
    setPaused,
    paused: data?.instance?.autoMaterializePaused,
    refetch,
  };
}

export const AUTOMATERIALIZE_PAUSED_QUERY = gql`
  query GetAutoMaterializePausedQuery {
    instance {
      id
      autoMaterializePaused
    }
  }
`;

export const SET_AUTOMATERIALIZE_PAUSED_MUTATION = gql`
  mutation SetAutoMaterializePausedMutation($paused: Boolean!) {
    setAutoMaterializePaused(paused: $paused)
  }
`;
