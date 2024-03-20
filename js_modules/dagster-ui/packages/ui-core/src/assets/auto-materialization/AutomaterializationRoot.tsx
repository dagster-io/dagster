import {Heading, Page, PageHeader} from '@dagster-io/ui-components';
import {Redirect} from 'react-router-dom';

import {GlobalAutomaterializationContent} from './GlobalAutomaterializationContent';
import {assertUnreachable} from '../../app/Util';
import {useTrackPageView} from '../../app/analytics';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {OverviewTabs} from '../../overview/OverviewTabs';
import {useAutoMaterializeSensorFlag} from '../AutoMaterializeSensorFlag';

// Determine whether the user is flagged to see automaterialize policies as
// sensors. If so, redirect to the Sensors overview.
export const AutomaterializationRoot = () => {
  const automaterializeSensorsFlagState = useAutoMaterializeSensorFlag();
  switch (automaterializeSensorsFlagState) {
    case 'unknown':
      return <div />; // Waiting for result
    case 'has-global-amp':
      return <GlobalAutomaterializationRoot />;
    case 'has-sensor-amp':
      return <Redirect to="/overview/sensors" />;
    default:
      assertUnreachable(automaterializeSensorsFlagState);
  }
};

const GlobalAutomaterializationRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Auto-materialize');
  return (
    <Page>
      <PageHeader title={<Heading>Overview</Heading>} tabs={<OverviewTabs tab="amp" />} />
      <GlobalAutomaterializationContent />
    </Page>
  );
};
