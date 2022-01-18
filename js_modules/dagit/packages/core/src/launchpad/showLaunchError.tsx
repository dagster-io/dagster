import {FontFamily} from '@dagster-io/ui';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';

export const showLaunchError = (error: Error) => {
  console.error('Error launching run:', error);

  const body =
    error.message === 'Failed to fetch' ? (
      <div style={{fontFamily: FontFamily.default}}>
        Make sure the Dagit server is running and try again.
      </div>
    ) : (
      <div>{error.message}</div>
    );

  showCustomAlert({
    title: 'Could not launch run',
    body,
  });
};
