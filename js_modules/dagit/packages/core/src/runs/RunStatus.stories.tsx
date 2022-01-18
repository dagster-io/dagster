import {Box, MetadataTable} from '@dagster-io/ui';
import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {RunStatus} from '../types/globalTypes';

import {RunStatusIndicator} from './RunStatusDots';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunStatus',
  component: RunStatusIndicator,
} as Meta;

export const Example = () => {
  return (
    <MetadataTable
      rows={Object.values(RunStatus).map((value: RunStatus) => ({
        key: value,
        value: (
          <Box padding={{top: 2}}>
            <RunStatusIndicator status={value} />
          </Box>
        ),
      }))}
    />
  );
};
