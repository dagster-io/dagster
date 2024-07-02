import {gql, useMutation, useQuery} from '@apollo/client';
import {Checkbox, Colors, Icon, Spinner, Tooltip} from '@dagster-io/ui-components';

import {
  START_SCHEDULE_MUTATION,
  STOP_SCHEDULE_MUTATION,
  displayScheduleMutationErrors,
} from './ScheduleMutations';
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
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
  schedule: ScheduleSwitchFragment;
  size?: 'small' | 'large';
  shouldFetchLatestState?: boolean;
}

export const ScheduleSwitch = (props: Props) => {
  const {repoAddress, schedule, size = 'large', shouldFetchLatestState} = props;
  const {name, scheduleState} = schedule;
  const {id, selectorId} = scheduleState;

  const {
    permissions: {canStartSchedule, canStopRunningSchedule},
    disabledReasons,
  } = usePermissionsForLocation(repoAddress.location);

  const scheduleSelector = {
    ...repoAddressToSelector(repoAddress),
    scheduleName: name,
  };

  const {data, loading} = useQuery<ScheduleStateQuery, ScheduleStateQueryVariables>(
    SCHEDULE_STATE_QUERY,
    {
      variables: {scheduleSelector},
      skip: !shouldFetchLatestState,
    },
  );

  const [startSchedule, {loading: toggleOnInFlight}] = useMutation<
    StartThisScheduleMutation,
    StartThisScheduleMutationVariables
  >(START_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });
  const [stopSchedule, {loading: toggleOffInFlight}] = useMutation<
    StopScheduleMutation,
    StopScheduleMutationVariables
  >(STOP_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });

  const onStatusChange = () => {
    if (status === InstigationStatus.RUNNING) {
      stopSchedule({
        variables: {scheduleOriginId: id, scheduleSelectorId: selectorId},
      });
    } else {
      startSchedule({
        variables: {scheduleSelector},
      });
    }
  };

  if (shouldFetchLatestState && !data && loading) {
    return <Spinner purpose="body-text" />;
  }

  if (shouldFetchLatestState && data?.scheduleOrError.__typename !== 'Schedule') {
    return (
      <Tooltip content="Error loading schedule state">
        <Icon name="error" color={Colors.accentRed()} />;
      </Tooltip>
    );
  }

  const status = shouldFetchLatestState
    ? // @ts-expect-error - we refined the type based on shouldFetchLatestState above
      data.scheduleOrError.scheduleState.status
    : schedule.scheduleState.status;
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
  fragment ScheduleSwitchFragment on InstigationState {
    id
    selectorId
    status
  }
`;

const SCHEDULE_STATE_QUERY = gql`
  query ScheduleStateQuery($id: String!) {
    instigationStateOrError(id: $id) {
      ... on InstigationState {
        id
        status
      }
    }
  }
`;
