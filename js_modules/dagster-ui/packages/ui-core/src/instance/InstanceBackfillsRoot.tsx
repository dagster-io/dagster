import {Heading, Page, PageHeader} from '@dagster-io/ui-components';

import {InstanceBackfills} from './InstanceBackfills';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {OverviewTabs} from '../overview/OverviewTabs';

export const InstanceBackfillsRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Backfills');

  return (
    <Page>
      <PageHeader title={<Heading>Overview</Heading>} tabs={<OverviewTabs tab="backfills" />} />
      <InstanceBackfills />
    </Page>
  );
};
