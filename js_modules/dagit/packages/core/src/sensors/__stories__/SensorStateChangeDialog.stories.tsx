import {MockedProvider} from '@apollo/client/testing';
import {Button} from '@dagster-io/ui';
import {Meta} from '@storybook/react';
import * as React from 'react';

import {OpenWithIntent} from '../../instigation/useInstigationStateReducer';
import {SensorStateChangeDialog} from '../SensorStateChangeDialog';
import {
  buildStartKansasSuccess,
  buildStartLouisianaError,
  buildStartLouisianaSuccess,
  buildStopMinnesotaSuccess,
  buildStopOregonSuccess,
  sensorKansasCurrentlyStopped,
  sensorLouisianaCurrentlyStopped,
  sensorMinnesotaCurrentlyRunning,
  sensorOregonCurrentlyRunning,
} from '../__fixtures__/SensorState.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'SensorStateChangeDialog',
  component: SensorStateChangeDialog,
} as Meta;

export const StartSensors = () => {
  const [dialogState, setDialogState] = React.useState<OpenWithIntent>('not-open');

  return (
    <MockedProvider mocks={[buildStartKansasSuccess(1000), buildStartLouisianaSuccess(1000)]}>
      <>
        <Button onClick={() => setDialogState('start')}>Start sensors</Button>
        <SensorStateChangeDialog
          sensors={[sensorKansasCurrentlyStopped, sensorLouisianaCurrentlyStopped]}
          onClose={() => setDialogState('not-open')}
          onComplete={() => {}}
          openWithIntent={dialogState}
        />
      </>
    </MockedProvider>
  );
};

export const StopSensors = () => {
  const [dialogState, setDialogState] = React.useState<OpenWithIntent>('not-open');

  return (
    <MockedProvider mocks={[buildStopMinnesotaSuccess(1000), buildStopOregonSuccess(1000)]}>
      <>
        <Button onClick={() => setDialogState('stop')}>Stop sensors</Button>
        <SensorStateChangeDialog
          sensors={[sensorMinnesotaCurrentlyRunning, sensorOregonCurrentlyRunning]}
          onClose={() => setDialogState('not-open')}
          onComplete={() => {}}
          openWithIntent={dialogState}
        />
      </>
    </MockedProvider>
  );
};

export const StartSensorsWithError = () => {
  const [dialogState, setDialogState] = React.useState<OpenWithIntent>('not-open');

  return (
    <MockedProvider mocks={[buildStartKansasSuccess(1000), buildStartLouisianaError(1000)]}>
      <>
        <Button onClick={() => setDialogState('start')}>Start sensors</Button>
        <SensorStateChangeDialog
          sensors={[sensorKansasCurrentlyStopped, sensorLouisianaCurrentlyStopped]}
          onClose={() => setDialogState('not-open')}
          onComplete={() => {}}
          openWithIntent={dialogState}
        />
      </>
    </MockedProvider>
  );
};
