import {Colors, Icon, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {LeftNavItemType} from './LeftNavItemType';
import {Item} from './RepositoryContentList';
import {ScheduleAndSensorDialog} from './ScheduleAndSensorDialog';
import {InstigationStatus} from '../graphql/types';
import {humanCronString} from '../schedules/humanCronString';
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

    const rightIcon = () => {
      const scheduleCount = schedules.length;
      const sensorCount = sensors.length;

      if (!scheduleCount && !sensorCount) {
        return null;
      }

      const whichIcon = scheduleCount ? 'schedule' : 'sensors';
      const needsDialog = scheduleCount > 1 || sensorCount > 1 || (scheduleCount && sensorCount);

      const status = () => {
        return schedules.some(
          (schedule) => schedule.scheduleState.status === InstigationStatus.RUNNING,
        ) || sensors.some((sensor) => sensor.sensorState.status === InstigationStatus.RUNNING)
          ? InstigationStatus.RUNNING
          : InstigationStatus.STOPPED;
      };

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
              status() === InstigationStatus.RUNNING ? Colors.accentGreen() : Colors.accentGray()
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
    };

    return (
      <ItemContainer ref={ref}>
        <Item $active={active} to={path}>
          <Icon name={leftIcon} color={active ? Colors.accentBlue() : Colors.textDefault()} />
          {label}
        </Item>
        {rightIcon()}
      </ItemContainer>
    );
  },
);

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
