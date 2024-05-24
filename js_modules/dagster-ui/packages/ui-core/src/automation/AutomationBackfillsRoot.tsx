import {Heading, Page, PageHeader} from '@dagster-io/ui-components';

import {AutomationTabs} from './AutomationTabs';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {InstanceBackfills} from '../instance/InstanceBackfills';

export const AutomationBackfillsRoot = () => {
  useTrackPageView();
  useDocumentTitle('Automation | Backfills');

  return (
    <Page>
      <PageHeader title={<Heading>Automation</Heading>} tabs={<AutomationTabs tab="backfills" />} />
      <InstanceBackfills />
    </Page>
  );
};
