// eslint-disable-next-line no-restricted-imports
import * as React from 'react';
import {Meta} from '@storybook/react';
import {GraphQLError} from 'graphql';

import {AppStackTraceLink} from '../AppError';
import {CustomAlertProvider} from '../CustomAlertProvider';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'AppStackTraceLink',
} as Meta;

export const Default = () => {
  const error = new GraphQLError('failure');
  return (
    <>
      <CustomAlertProvider />
      <AppStackTraceLink error={error} operationName="FooQuery" />
    </>
  );
};
