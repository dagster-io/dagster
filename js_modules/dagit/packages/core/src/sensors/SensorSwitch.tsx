import {useMutation} from '@apollo/client';
import {Checkbox, Tooltip} from '@dagster-io/ui';
import * as React from 'react';

import {usePermissionsForLocation} from '../app/Permissions';
import {graphql} from '../graphql';
import {InstigationStatus, SensorSwitchFragmentFragment} from '../graphql/graphql';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {
  displaySensorMutationErrors,
  START_SENSOR_MUTATION,
  STOP_SENSOR_MUTATION,
} from './SensorMutations';

interface Props {
  repoAddress: RepoAddress;
  sensor: SensorSwitchFragmentFragment;
  size?: 'small' | 'large';
}

export const SensorSwitch: React.FC<Props> = (props) => {
  const {repoAddress, sensor, size = 'large'} = props;
  const {canStartSensor, canStopSensor} = usePermissionsForLocation(repoAddress.location);

  const {jobOriginId, name, sensorState} = sensor;
  const {status, selectorId} = sensorState;
  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName: name,
  };

  const [startSensor, {loading: toggleOnInFlight}] = useMutation(START_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
  });
  const [stopSensor, {loading: toggleOffInFlight}] = useMutation(STOP_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
  });

  const onChangeSwitch = () => {
    if (status === InstigationStatus.RUNNING) {
      stopSensor({variables: {jobOriginId, jobSelectorId: selectorId}});
    } else {
      startSensor({variables: {sensorSelector}});
    }
  };

  const running = status === InstigationStatus.RUNNING;

  if (canStartSensor.enabled && canStopSensor.enabled) {
    return (
      <Checkbox
        format="switch"
        disabled={toggleOnInFlight || toggleOffInFlight}
        checked={running || toggleOnInFlight}
        onChange={onChangeSwitch}
        size={size}
      />
    );
  }

  const lacksPermission =
    (running && !canStartSensor.enabled) || (!running && !canStopSensor.enabled);
  const disabled = toggleOffInFlight || toggleOnInFlight || lacksPermission;

  const switchElement = (
    <Checkbox
      format="switch"
      disabled={disabled}
      checked={running || toggleOnInFlight}
      onChange={onChangeSwitch}
      size={size}
    />
  );

  return lacksPermission ? (
    <Tooltip
      content={running ? canStartSensor.disabledReason : canStopSensor.disabledReason}
      display="flex"
    >
      {switchElement}
    </Tooltip>
  ) : (
    switchElement
  );
};

export const SENSOR_SWITCH_FRAGMENT = graphql(`
  fragment SensorSwitchFragment on Sensor {
    id
    jobOriginId
    name
    sensorState {
      id
      selectorId
      status
    }
  }
`);
