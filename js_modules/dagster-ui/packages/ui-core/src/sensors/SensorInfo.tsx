import {Alert, Box} from '@dagster-io/ui-components';
import * as React from 'react';

export type DaemonStatusForWarning = {
  healthy: boolean | null;
  required: boolean | null;
};

type Props = React.ComponentPropsWithRef<typeof Box> & {
  sensorDaemonStatus?: DaemonStatusForWarning;
  assetDaemonStatus?: DaemonStatusForWarning;
};

export const SensorInfo = ({sensorDaemonStatus, assetDaemonStatus, ...boxProps}: Props) => {
  const warnForSensor =
    sensorDaemonStatus && sensorDaemonStatus.healthy === false && sensorDaemonStatus.required;
  const warnForAssets =
    assetDaemonStatus && !assetDaemonStatus.healthy === false && assetDaemonStatus.required;

  if (!warnForAssets && !warnForSensor) {
    return null;
  }

  const title = () => {
    if (warnForSensor) {
      if (warnForAssets) {
        return 'The sensor and asset daemons are not running';
      }
      return 'The sensor daemon is not running';
    }
    return 'The asset daemon is not running';
  };

  return (
    <Box {...boxProps}>
      <Alert
        intent="warning"
        title={title()}
        description={
          <div>
            See the{' '}
            <a
              href="https://docs.dagster.io/deployment/dagster-daemon"
              target="_blank"
              rel="noreferrer"
            >
              dagster-daemon documentation
            </a>{' '}
            for more information on how to deploy the dagster-daemon process.
          </div>
        }
      />
    </Box>
  );
};
