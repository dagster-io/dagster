import {Box, PageHeader} from '@dagster-io/ui-components';
import React from 'react';
import {OverviewPageAlerts} from 'shared/overview/OverviewPageAlerts.oss';

import {OverviewTabs} from './OverviewTabs';

export const OverviewPageHeader = ({
  tab,
  queryData,
  refreshState,
  ...rest
}: React.ComponentProps<typeof OverviewTabs> &
  Omit<React.ComponentProps<typeof PageHeader>, 'title'>) => {
  return (
    <PageHeader
      tabs={
        <Box flex={{direction: 'column', gap: 8}}>
          <OverviewTabs tab={tab} queryData={queryData} refreshState={refreshState} />
          <OverviewPageAlerts />
        </Box>
      }
      {...rest}
    />
  );
};
