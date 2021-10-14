import {gql, useMutation} from '@apollo/client';
import * as React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {InstigationType} from '../types/globalTypes';
import {ButtonLink} from '../ui/ButtonLink';
import {Tooltip} from '../ui/Tooltip';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {SCHEDULES_ROOT_QUERY} from './ScheduleUtils';
import {ReconcileSchedulerState} from './types/ReconcileSchedulerState';

export const ReconcileButton: React.FC<{repoAddress: RepoAddress}> = ({repoAddress}) => {
  const {canReconcileSchedulerState} = usePermissions();
  const repositorySelector = repoAddressToSelector(repoAddress);
  const refetchQueries = [
    {
      query: SCHEDULES_ROOT_QUERY,
      variables: {
        repositorySelector: repositorySelector,
        instigationType: InstigationType.SCHEDULE,
      },
    },
  ];

  const [
    reconcileScheduleState,
    {loading: reconcileInFlight},
  ] = useMutation<ReconcileSchedulerState>(RECONCILE_SCHEDULE_STATE_MUTATION, {refetchQueries});

  if (!canReconcileSchedulerState) {
    return (
      <Tooltip content={DISABLED_MESSAGE}>
        <ButtonLink underline="always" disabled>
          Reconcile
        </ButtonLink>
      </Tooltip>
    );
  }

  return (
    <ButtonLink
      underline="always"
      disabled={reconcileInFlight}
      onClick={() => reconcileScheduleState({variables: {repositorySelector}})}
    >
      Reconcile
    </ButtonLink>
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
