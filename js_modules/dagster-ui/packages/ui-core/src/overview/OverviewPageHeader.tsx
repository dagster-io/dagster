import {Box, PageHeader} from '@dagster-io/ui-components';
import {observeEnabled} from '@shared/app/observeEnabled';
import React from 'react';

import {ObserveRolloutBanner} from './ObserveRolloutBanner';
import {OverviewTabs} from './OverviewTabs';

export const OverviewPageHeader = ({
  tab,
  queryData,
  refreshState,
  ...rest
}: React.ComponentProps<typeof OverviewTabs> &
  Omit<React.ComponentProps<typeof PageHeader>, 'title'>) => {
  const observeUIEnabled = observeEnabled();
  if (observeUIEnabled) {
    return null;
  }

  return (
    <div>
      <ObserveRolloutBanner />
      <PageHeader
        tabs={
          <Box flex={{direction: 'column', gap: 8}}>
            <OverviewTabs tab={tab} queryData={queryData} refreshState={refreshState} />
          </Box>
        }
        {...rest}
      />
    </div>
  );
};
