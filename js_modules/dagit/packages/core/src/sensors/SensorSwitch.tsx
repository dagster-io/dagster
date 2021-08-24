import {gql, useMutation} from '@apollo/client';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {InstigationStatus} from '../types/globalTypes';
import {SwitchWithoutLabel} from '../ui/SwitchWithoutLabel';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {
  displaySensorMutationErrors,
  START_SENSOR_MUTATION,
  STOP_SENSOR_MUTATION,
} from './SensorMutations';
import {SensorSwitchFragment} from './types/SensorSwitchFragment';
import {StartSensor} from './types/StartSensor';
import {StopSensor} from './types/StopSensor';

interface Props {
  large?: boolean;
  repoAddress: RepoAddress;
  sensor: SensorSwitchFragment;
}

export const SensorSwitch: React.FC<Props> = (props) => {
  const {large = true, repoAddress, sensor} = props;
  const {canStartSensor, canStopSensor} = usePermissions();

  const {jobOriginId, name, sensorState} = sensor;
  const {status} = sensorState;
  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName: name,
  };

  const [startSensor, {loading: toggleOnInFlight}] = useMutation<StartSensor>(
    START_SENSOR_MUTATION,
    {onCompleted: displaySensorMutationErrors},
  );
  const [stopSensor, {loading: toggleOffInFlight}] = useMutation<StopSensor>(STOP_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
  });

  const onChangeSwitch = () => {
    if (status === InstigationStatus.RUNNING) {
      stopSensor({variables: {jobOriginId}});
    } else {
      startSensor({variables: {sensorSelector}});
    }
  };

  const running = status === InstigationStatus.RUNNING;

  if (canStartSensor && canStopSensor) {
    return (
      <SwitchWithoutLabel
        disabled={toggleOnInFlight || toggleOffInFlight}
        large={large}
        innerLabelChecked="on"
        innerLabel="off"
        checked={running || toggleOnInFlight}
        onChange={onChangeSwitch}
      />
    );
  }

  const lacksPermission = (running && !canStartSensor) || (!running && !canStopSensor);
  const disabled = toggleOffInFlight || toggleOnInFlight || lacksPermission;

  return (
    <Tooltip content={lacksPermission ? DISABLED_MESSAGE : undefined}>
      <SwitchWithoutLabel
        disabled={disabled}
        large={large}
        innerLabelChecked="on"
        innerLabel="off"
        checked={running || toggleOnInFlight}
        onChange={onChangeSwitch}
      />
    </Tooltip>
  );
};

export const SENSOR_SWITCH_FRAGMENT = gql`
  fragment SensorSwitchFragment on Sensor {
    id
    jobOriginId
    name
    sensorState {
      id
      status
    }
  }
`;
