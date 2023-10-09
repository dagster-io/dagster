import {gql, useMutation, useQuery} from '@apollo/client';
import {Tag, Tooltip} from '@dagster-io/ui-components';
import React, {useCallback} from 'react';
import {Link} from 'react-router-dom';

import {
  GetAutoMaterializePausedQuery,
  GetAutoMaterializePausedQueryVariables,
  SetAutoMaterializePausedMutation,
  SetAutoMaterializePausedMutationVariables,
} from './types/AutomaterializeDaemonStatusTag.types';

export const AutomaterializeDaemonStatusTag = () => {
  const {paused} = useAutomaterializeDaemonStatus();

  return (
    <Tooltip
      content={
        paused
          ? 'Auto-materializing is paused. New materializations will not be triggered by auto-materialization policies.'
          : ''
      }
      canShow={paused}
    >
      <Link to="/health" style={{outline: 'none'}}>
        <Tag icon={paused ? 'toggle_off' : 'toggle_on'} intent={paused ? 'warning' : 'success'}>
          {paused ? 'Auto-materialize off' : 'Auto-materialize on'}
        </Tag>
      </Link>
    </Tooltip>
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
