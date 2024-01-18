import * as React from 'react';

import {FontFamily} from '@dagster-io/ui-components';

import {showCustomAlert} from '../app/CustomAlertProvider';

export const showLaunchError = (error: Error) => {
  console.error('Error launching run:', error);

  const body =
    error.message === 'Failed to fetch' ? (
      <div style={{fontFamily: FontFamily.default}}>
        Make sure the Dagster webserver is running and try again.
      </div>
    ) : (
      <div>{error.message}</div>
    );

  showCustomAlert({
    title: 'Could not launch run',
    body,
  });
};
