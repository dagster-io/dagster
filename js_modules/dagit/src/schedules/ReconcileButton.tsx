import {Button, Intent, Spinner} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import {useMutation} from 'react-apollo';

import {useRepositorySelector} from 'src/DagsterRepositoryContext';
import {SCHEDULES_ROOT_QUERY} from 'src/schedules/ScheduleUtils';

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
