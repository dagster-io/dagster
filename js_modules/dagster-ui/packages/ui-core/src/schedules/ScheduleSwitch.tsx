import {Box, Checkbox, Colors, Icon, Spinner, Tooltip} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {
  START_SCHEDULE_MUTATION,
  STOP_SCHEDULE_MUTATION,
  displayScheduleMutationErrors,
} from './ScheduleMutations';
import {gql, useMutation, useQuery} from '../apollo-client';
import {
  StartThisScheduleMutation,
  StartThisScheduleMutationVariables,
  StopScheduleMutation,
  StopScheduleMutationVariables,
} from './types/ScheduleMutations.types';
import {
  ScheduleStateQuery,
  ScheduleStateQueryVariables,
  ScheduleSwitchFragment,
} from './types/ScheduleSwitch.types';
import {usePermissionsForLocation} from '../app/Permissions';
import {InstigationStatus} from '../graphql/types';
import {INSTIGATION_STATE_BASE_FRAGMENT} from '../instigation/InstigationStateBaseFragment';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
  schedule: ScheduleSwitchFragment;
  size?: 'small' | 'large';
}

export const ScheduleSwitch = (props: Props) => {
  const {repoAddress, schedule, size = 'large'} = props;
  const {name, scheduleState} = schedule;
  const {id} = scheduleState;

  const {
    permissions: {canStartSchedule, canStopRunningSchedule},
    disabledReasons,
  } = usePermissionsForLocation(repoAddress.location);

  const repoAddressSelector = useMemo(() => repoAddressToSelector(repoAddress), [repoAddress]);

  const variables = {
    id: schedule.id,
    selector: {
      ...repoAddressSelector,
      name,
    },
  };

  const {data, loading} = useQuery<ScheduleStateQuery, ScheduleStateQueryVariables>(
    SCHEDULE_STATE_QUERY,
    {variables},
  );

  const [startSchedule, {loading: toggleOnInFlight}] = useMutation<
    StartThisScheduleMutation,
    StartThisScheduleMutationVariables
  >(START_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
    refetchQueries: [{variables, query: SCHEDULE_STATE_QUERY}],
    awaitRefetchQueries: true,
  });
  const [stopSchedule, {loading: toggleOffInFlight}] = useMutation<
    StopScheduleMutation,
    StopScheduleMutationVariables
  >(STOP_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
    refetchQueries: [{variables, query: SCHEDULE_STATE_QUERY}],
    awaitRefetchQueries: true,
  });

  const onStatusChange = () => {
    if (status === InstigationStatus.RUNNING) {
      stopSchedule({
        variables: {id},
      });
    } else {
      startSchedule({
        variables: {
          scheduleSelector: {
            ...repoAddressSelector,
            scheduleName: name,
          },
        },
      });
    }
  };

  // Status according to schedule object passed in (may be outdated if its from the workspace snapshot)
  let status = schedule.scheduleState.status;

  if (!data && loading) {
    return (
      <Box flex={{direction: 'row', justifyContent: 'center'}} style={{width: '30px'}}>
        <Spinner purpose="body-text" />
      </Box>
    );
  }
  if (
    !['InstigationState', 'InstigationStateNotFoundError'].includes(
      data?.instigationStateOrError.__typename as any,
    )
  ) {
    return (
      <Tooltip content="Error loading schedule state">
        <Icon name="error" color={Colors.accentRed()} />;
      </Tooltip>
    );
  } else if (data?.instigationStateOrError.__typename === 'InstigationState') {
    // status according to latest data
    status = data?.instigationStateOrError.status;
  }

  const running = status === InstigationStatus.RUNNING;

  if (canStartSchedule && canStopRunningSchedule) {
    return (
      <Checkbox
        format="switch"
        checked={running || toggleOnInFlight}
        disabled={toggleOffInFlight || toggleOnInFlight}
        onChange={onStatusChange}
        size={size}
      />
    );
  }

  const lacksPermission = (running && !canStopRunningSchedule) || (!running && !canStartSchedule);
  const disabled = toggleOffInFlight || toggleOnInFlight || lacksPermission;

  const switchElement = (
    <Checkbox
      format="switch"
      checked={running || toggleOnInFlight}
      disabled={disabled}
      onChange={onStatusChange}
      size={size}
    />
  );

  if (!lacksPermission) {
    return switchElement;
  }

  const disabledReason = running
    ? disabledReasons.canStopRunningSchedule
    : disabledReasons.canStartSchedule;

  return (
    <Tooltip content={disabledReason} display="flex">
      {switchElement}
    </Tooltip>
  );
};

export const SCHEDULE_SWITCH_FRAGMENT = gql`
  fragment ScheduleSwitchFragment on Schedule {
    id
    name
    cronSchedule
    executionTimezone
    scheduleState {
      id
      selectorId
      status
    }
  }
`;

const SCHEDULE_STATE_QUERY = gql`
  query ScheduleStateQuery($id: String!, $selector: InstigationSelector!) {
    instigationStateOrError(id: $id, instigationSelector: $selector) {
      ... on InstigationState {
        id
        ...InstigationStateBaseFragment
      }
    }
  }
  ${INSTIGATION_STATE_BASE_FRAGMENT}
`;
