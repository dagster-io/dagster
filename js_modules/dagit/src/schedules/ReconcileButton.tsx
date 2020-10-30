import {gql, useMutation} from '@apollo/client';
import {Button, Intent, Spinner} from '@blueprintjs/core';
import * as React from 'react';

import {SCHEDULES_ROOT_QUERY} from 'src/schedules/ScheduleUtils';
import {useRepositorySelector} from 'src/workspace/WorkspaceContext';

export const ReconcileButton: React.FunctionComponent<{}> = () => {
  const repositorySelector = useRepositorySelector();
  const refetchQueries = [
    {
      query: SCHEDULES_ROOT_QUERY,
      variables: {
        repositorySelector: repositorySelector,
      },
    },
  ];

  const [
    reconcileScheduleState,
    {loading: reconcileInFlight},
  ] = useMutation(RECONCILE_SCHEDULE_STATE_MUTATION, {refetchQueries});

  if (reconcileInFlight) {
    return <Spinner />;
  }

  return (
    <Button
      small={true}
      intent={Intent.SUCCESS}
      onClick={() => reconcileScheduleState({variables: {repositorySelector}})}
    >
      Reconcile
    </Button>
  );
};

const RECONCILE_SCHEDULE_STATE_MUTATION = gql`
  mutation ReconcileSchedulerState($repositorySelector: RepositorySelector!) {
    reconcileSchedulerState(repositorySelector: $repositorySelector) {
      __typename
      ... on PythonError {
        message
        stack
      }
      ... on ReconcileSchedulerStateSuccess {
        __typename
        message
      }
    }
  }
`;
