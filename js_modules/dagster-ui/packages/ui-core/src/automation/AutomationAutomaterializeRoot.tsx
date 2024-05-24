import {Heading, Page, PageHeader} from '@dagster-io/ui-components';
import {Redirect} from 'react-router-dom';

import {AutomationTabs} from './AutomationTabs';
import {assertUnreachable} from '../app/Util';
import {useTrackPageView} from '../app/analytics';
import {useAutoMaterializeSensorFlag} from '../assets/AutoMaterializeSensorFlag';
import {GlobalAutomaterializationContent} from '../assets/auto-materialization/GlobalAutomaterializationContent';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

// Determine whether the user is flagged to see automaterialize policies as
// sensors. If so, redirect to the Sensors overview.
export const AutomationAutomaterializeRoot = () => {
  const automaterializeSensorsFlagState = useAutoMaterializeSensorFlag();
  switch (automaterializeSensorsFlagState) {
    case 'unknown':
      return <div />; // Waiting for result
    case 'has-global-amp':
      return <GlobalAutomationAutomaterializeRoot />;
    case 'has-sensor-amp':
      return <Redirect to="/automation/sensors" />;
    default:
      assertUnreachable(automaterializeSensorsFlagState);
  }
};

const GlobalAutomationAutomaterializeRoot = () => {
  useTrackPageView();
  useDocumentTitle('Automation | Auto-materialize');
  return (
    <Page>
      <PageHeader title={<Heading>Automation</Heading>} tabs={<AutomationTabs tab="amp" />} />
      <GlobalAutomaterializationContent />
    </Page>
  );
};
