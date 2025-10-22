import {Button, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';

import {RESET_SENSOR_MUTATION, displaySensorMutationErrors} from './SensorMutations';
import {useMutation} from '../apollo-client';
import {SensorFragment} from './types/SensorFragment.types';
import {ResetSensorMutation, ResetSensorMutationVariables} from './types/SensorMutations.types';
import {DEFAULT_DISABLED_REASON} from '../app/Permissions';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
  sensor: SensorFragment;
}

export const SensorResetButton = ({repoAddress, sensor}: Props) => {
  const {name} = sensor;
  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName: name,
  };

  const [resetSensor, {loading: toggleOnInFlight}] = useMutation<
    ResetSensorMutation,
    ResetSensorMutationVariables
  >(RESET_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
  });
  const onClick = () => {
    resetSensor({variables: {sensorSelector}});
  };

  const hasPermission =
    sensor.sensorState.hasStartPermission && sensor.sensorState.hasStopPermission;
  const disabled = toggleOnInFlight || !hasPermission;
  const tooltipContent = hasPermission
    ? `In code, a default status for "${name}" has been set to "${sensor.defaultStatus}". Click here to reset the sensor status to track the status set in code.`
    : DEFAULT_DISABLED_REASON;

  return (
    <Tooltip
      content={<div style={{maxWidth: '500px', wordBreak: 'break-word'}}>{tooltipContent}</div>}
      display="flex"
    >
      <Button disabled={disabled} onClick={onClick}>
        Reset sensor status
      </Button>
    </Tooltip>
  );
};
