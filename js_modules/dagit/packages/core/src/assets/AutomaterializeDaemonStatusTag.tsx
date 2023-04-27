import {gql, useMutation, useQuery} from '@apollo/client';
import {Tag, Tooltip} from '@dagster-io/ui';
import React, {useCallback} from 'react';
import {Link} from 'react-router-dom';

import {
  GetAutoMaterializePausedQuery,
  GetAutoMaterializePausedQueryVariables,
  SetAutoMaterializePausedMutation,
  SetAutoMaterializePausedMutationVariables,
} from './types/AutomaterializeDaemonStatusTag.types';

export const AutomaterializeDaemonStatusTag: React.FC = () => {
  const {paused} = useAutomaterializeDaemonStatus();

  return (
    <Link to="/health">
      {paused ? (
        <Tooltip content="Auto-materializing is paused. New materializations will not be triggered by auto-materialization policies.">
          <Tag icon="toggle_off" intent="warning">
            Auto-materialize
          </Tag>
        </Tooltip>
      ) : (
        <Tag icon="toggle_on" intent="success">
          Auto-materialize
        </Tag>
      )}
    </Link>
  );
};

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

  const setPaused = useCallback(
    (paused: boolean) => {
      setAutoMaterializePaused({variables: {paused}});
    },
    [setAutoMaterializePaused],
  );

  return {
    loading,
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
