import {Page} from '@dagster-io/ui-components';

import {InstanceBackfills} from './InstanceBackfills';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {OverviewPageHeader} from '../overview/OverviewPageHeader';

export const InstanceBackfillsRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Backfills');

  return (
    <Page>
      <OverviewPageHeader tab="backfills" />
      <InstanceBackfills />
    </Page>
  );
};
