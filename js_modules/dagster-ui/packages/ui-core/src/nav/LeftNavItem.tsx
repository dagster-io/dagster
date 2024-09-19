import {Colors, Icon, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';
import {useEffect, useMemo, useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {LeftNavItemType} from './LeftNavItemType';
import {Item} from './RepositoryContentList';
import {ScheduleAndSensorDialog} from './ScheduleAndSensorDialog';
import {InstigationStatesQuery, InstigationStatesQueryVariables} from './types/LeftNavItem.types';
import {gql, useFragment, useQuery} from '../apollo-client';
import {InstigationStatus} from '../graphql/types';
import {INSTIGATION_STATE_BASE_FRAGMENT} from '../instigation/InstigationStateBaseFragment';
import {InstigationStateFragment} from '../instigation/types/InstigationUtils.types';
import {humanCronString} from '../schedules/humanCronString';
import {useRepository} from '../workspace/WorkspaceContext/util';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface LeftNavItemProps {
  active: boolean;
  item: LeftNavItemType;
}

export const LeftNavItem = React.forwardRef(
  (props: LeftNavItemProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {active, item} = props;
    const {label, leftIcon, path, repoAddress, schedules, sensors} = item;

    const [showDialog, setShowDialog] = React.useState(false);
    const repositoryId = useRepository(repoAddress)?.repository.id;

    useQuery<InstigationStatesQuery, InstigationStatesQueryVariables>(INSTIGATION_STATES_QUERY, {
      variables: {
        repositoryID: repositoryId!,
      },
      skip: !repositoryId,
    });
    const [data, setData] = useState<Record<string, InstigationStateFragment>>({});

    const status = useMemo(() => {
      const anyScheduleIsRunning = schedules.some((schedule) => {
        const state = data[schedule.id];
        return (state?.status ?? schedule.scheduleState.status) === InstigationStatus.RUNNING;
      });
      const anySensorIsRunning = sensors.some((sensor) => {
        const state = data[sensor.id];
        return (state?.status ?? sensor.sensorState.status) === InstigationStatus.RUNNING;
      });
      return anyScheduleIsRunning || anySensorIsRunning
        ? InstigationStatus.RUNNING
        : InstigationStatus.STOPPED;
    }, [schedules, sensors, data]);

    const rightIcon = useMemo(() => {
      const scheduleCount = schedules.length;
      const sensorCount = sensors.length;

      if (!scheduleCount && !sensorCount) {
        return null;
      }

      const whichIcon = scheduleCount ? 'schedule' : 'sensors';
      const needsDialog = scheduleCount > 1 || sensorCount > 1 || (scheduleCount && sensorCount);

      const tooltipContent = () => {
        if (scheduleCount && sensorCount) {
          const scheduleString = scheduleCount > 1 ? `${scheduleCount} schedules` : '1 schedule';
          const sensorString = sensorCount > 1 ? `${sensorCount} sensors` : '1 sensor';
          return `${scheduleString}, ${sensorString}`;
        }

        if (scheduleCount) {
          if (scheduleCount === 1) {
            const schedule = schedules[0]!;
            const {cronSchedule, executionTimezone} = schedule;
            return (
              <div>
                Schedule:{' '}
                <strong>{humanCronString(cronSchedule, executionTimezone || 'UTC')}</strong>
              </div>
            );
          }

          return `${scheduleCount} schedules`;
        }

        return sensorCount === 1 ? (
          <div>
            Sensor: <strong>{sensors[0]!.name}</strong>
          </div>
        ) : (
          `${sensorCount} sensors`
        );
      };

      const link = () => {
        const icon = (
          <Icon
            name={whichIcon}
            color={
              status === InstigationStatus.RUNNING ? Colors.accentGreen() : Colors.accentGray()
            }
          />
        );

        if (needsDialog) {
          return (
            <SensorScheduleDialogButton onClick={() => setShowDialog(true)}>
              {icon}
            </SensorScheduleDialogButton>
          );
        }

        const path = scheduleCount
          ? `/schedules/${schedules[0]!.name}`
          : sensorCount
          ? `/sensors/${sensors[0]!.name}`
          : null;

        return path ? <Link to={workspacePathFromAddress(repoAddress, path)}>{icon}</Link> : null;
      };

      return (
        <>
          <IconWithTooltip content={tooltipContent()}>{link()}</IconWithTooltip>
          {needsDialog ? (
            <ScheduleAndSensorDialog
              isOpen={showDialog}
              onClose={() => setShowDialog(false)}
              repoAddress={repoAddress}
              schedules={schedules}
              sensors={sensors}
              showSwitch
            />
          ) : null}
        </>
      );
    }, [repoAddress, schedules, sensors, showDialog, status]);

    const setFragmentData = React.useCallback((fragment: InstigationStateFragment) => {
      setData((data) => {
        return {
          ...data,
          [fragment.id]: fragment,
        };
      });
    }, []);

    /**
     * This is pretty clowny but `INSTIGATION_STATES_QUERY` only returns instigation states for sensors/schedules that were  previously turned on or off.
     * A side effect of this is that if on a sensor/schedule page we toggle it on/off then the new instigation state does not propagate to our query
     * since our query may not have returned an instigation state for that ID. To work around this we rely on
     * `useFragment` to subscribe to the individual instigation state fragments so that updates from elsewhere in the app propagate here while relying
     * on our useQuery above to batch fetch instigation states for sensors/schedules that were turned on/off previously.
     */
    const sensorFragmentSubscriptions = useMemo(
      () =>
        sensors.map((sensors) => (
          <InstigationStateFragmentSubscriptionComponent
            key={sensors.id}
            id={sensors.id}
            setData={setFragmentData}
          />
        )),
      [sensors, setFragmentData],
    );
    const scheduleFragmentSubscriptions = useMemo(
      () =>
        schedules.map((schedule) => (
          <InstigationStateFragmentSubscriptionComponent
            key={schedule.id}
            id={schedule.id}
            setData={setFragmentData}
          />
        )),
      [schedules, setFragmentData],
    );

    return (
      <ItemContainer ref={ref}>
        {sensorFragmentSubscriptions}
        {scheduleFragmentSubscriptions}
        <Item $active={active} to={path}>
          <Icon name={leftIcon} color={active ? Colors.accentBlue() : Colors.textDefault()} />
          {label}
        </Item>
        {rightIcon}
      </ItemContainer>
    );
  },
);

const InstigationStateFragmentSubscriptionComponent = ({
  id,
  setData,
}: {
  id: string;
  setData: (data: InstigationStateFragment) => void;
}) => {
  const {data, complete} = useFragment<InstigationStateFragment>({
    fragment: INSTIGATION_STATE_BASE_FRAGMENT,
    from: {
      __typename: 'InstigationState',
      id,
    },
  });
  useEffect(() => {
    if (complete && data) {
      setData(data);
    }
  }, [data, complete, setData]);
  return null;
};

const SensorScheduleDialogButton = styled.button`
  background: transparent;
  padding: 0;
  margin: 0;
  border: 0;
  cursor: pointer;

  :focus,
  :active,
  :hover {
    outline: none;
  }
`;

const IconWithTooltip = styled(Tooltip)`
  position: absolute;
  right: 8px;
  top: 6px;

  & a:focus,
  & a:active {
    outline: none;
  }
`;

const ItemContainer = styled.div`
  position: relative;
`;

const INSTIGATION_STATES_QUERY = gql`
  query InstigationStatesQuery($repositoryID: String!) {
    instigationStatesOrError(repositoryID: $repositoryID) {
      ... on PythonError {
        message
        stack
      }
      ... on InstigationStates {
        results {
          id
          ...InstigationStateBaseFragment
        }
      }
    }
  }
  ${INSTIGATION_STATE_BASE_FRAGMENT}
`;
