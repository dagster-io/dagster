import {Box, Page, PageHeader, Subtitle1} from '@dagster-io/ui-components';
import {Redirect} from 'react-router-dom';
import {observeEnabled} from 'shared/app/observeEnabled.oss';

import {GlobalAutomaterializationContent} from './GlobalAutomaterializationContent';
import {assertUnreachable} from '../../app/Util';
import {useTrackPageView} from '../../app/analytics';
import {AutomationTabs} from '../../automation/AutomationTabs';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {OverviewPageHeader} from '../../overview/OverviewPageHeader';
import {useAutoMaterializeSensorFlag} from '../AutoMaterializeSensorFlag';

// Determine whether the user is flagged to see automaterialize policies as
// sensors. If so, redirect to either the merged Automations page or the Sensors overview,
// depending on their nav flag state.
export const AutomaterializationRoot = () => {
  const automaterializeSensorsFlagState = useAutoMaterializeSensorFlag();
  switch (automaterializeSensorsFlagState) {
    case 'unknown':
      return <div />; // Waiting for result
    case 'has-global-amp':
      return <GlobalAutomaterializationRoot />;
    case 'has-sensor-amp':
      return <Redirect to="/automation" />;
    default:
      assertUnreachable(automaterializeSensorsFlagState);
  }
};

const GlobalAutomaterializationRoot = () => {
  useTrackPageView();
  useDocumentTitle('Automations | Auto-materialize');
  const showTabs = observeEnabled();
  return (
    <Page>
      {showTabs ? (
        <>
          <PageHeader title={<Subtitle1>Automation</Subtitle1>} />
          <Box padding={{horizontal: 24}} border="bottom">
            <AutomationTabs tab="global-amp" />
          </Box>
        </>
      ) : (
        <OverviewPageHeader tab="amp" />
      )}
      <GlobalAutomaterializationContent />
    </Page>
  );
};
