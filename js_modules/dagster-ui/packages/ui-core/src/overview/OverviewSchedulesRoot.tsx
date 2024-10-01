import {Box} from '@dagster-io/ui-components';

import {OverviewPageHeader} from './OverviewPageHeader';
import {OverviewSchedules} from './OverviewSchedules';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

export const OverviewSchedulesRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Schedules');

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <OverviewPageHeader tab="schedules" />
      <OverviewSchedules />
    </Box>
  );
};
