import {Box} from '@dagster-io/ui-components';

import {OverviewPageHeader} from './OverviewPageHeader';
import {OverviewSensors} from './OverviewSensors';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

export const OverviewSensorsRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Sensors');

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <OverviewPageHeader tab="sensors" />
      <OverviewSensors />
    </Box>
  );
};
