import {gql, useMutation} from '@apollo/client';
import {Button, Intent} from '@blueprintjs/core';
import * as React from 'react';

import {JobType} from '../types/globalTypes';
import {Spinner} from '../ui/Spinner';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {SCHEDULES_ROOT_QUERY} from './ScheduleUtils';
import {ReconcileSchedulerState} from './types/ReconcileSchedulerState';

export const ReconcileButton: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  const repositorySelector = repoAddressToSelector(repoAddress);
  const refetchQueries = [
    {
      query: SCHEDULES_ROOT_QUERY,
      variables: {
        repositorySelector: repositorySelector,
        jobType: JobType.SCHEDULE,
      },
    },
  ];

  const [
    reconcileScheduleState,
    {loading: reconcileInFlight},
  ] = useMutation<ReconcileSchedulerState>(RECONCILE_SCHEDULE_STATE_MUTATION, {refetchQueries});

  if (reconcileInFlight) {
    return <Spinner purpose="body-text" />;
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
