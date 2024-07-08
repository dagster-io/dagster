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
  const {id} = scheduleState;

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
        variables: {id},
      });
    } else {
      startSchedule({
        variables: {scheduleSelector},
      });
    }
  };

  let status = schedule.scheduleState.status;

  if (shouldFetchLatestState) {
    if (!data && loading) {
      return <Spinner purpose="body-text" />;
    }

    if (data?.scheduleOrError.__typename !== 'Schedule') {
      return (
        <Tooltip content="Error loading schedule state">
          <Icon name="error" color={Colors.accentRed()} />;
        </Tooltip>
      );
    }

    status = data.scheduleOrError.scheduleState.status;
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
  query ScheduleStateQuery($scheduleSelector: ScheduleSelector!) {
    scheduleOrError(scheduleSelector: $scheduleSelector) {
      ... on Schedule {
        id
        scheduleState {
          id
          status
        }
      }
    }
  }
`;
