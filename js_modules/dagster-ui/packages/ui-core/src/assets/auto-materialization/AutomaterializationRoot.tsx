import {Page} from '@dagster-io/ui-components';
import {Redirect} from 'react-router-dom';

import {GlobalAutomaterializationContent} from './GlobalAutomaterializationContent';
import {useFeatureFlags} from '../../app/Flags';
import {assertUnreachable} from '../../app/Util';
import {useTrackPageView} from '../../app/analytics';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {OverviewPageHeader} from '../../overview/OverviewPageHeader';
import {useAutoMaterializeSensorFlag} from '../AutoMaterializeSensorFlag';

// Determine whether the user is flagged to see automaterialize policies as
// sensors. If so, redirect to either the merged Automations page or the Sensors overview,
// depending on their nav flag state.
export const AutomaterializationRoot = () => {
  const automaterializeSensorsFlagState = useAutoMaterializeSensorFlag();
  const {flagLegacyNav} = useFeatureFlags();
  switch (automaterializeSensorsFlagState) {
    case 'unknown':
      return <div />; // Waiting for result
    case 'has-global-amp':
      return <GlobalAutomaterializationRoot />;
    case 'has-sensor-amp':
      return <Redirect to={flagLegacyNav ? '/overview/sensors' : '/automation'} />;
    default:
      assertUnreachable(automaterializeSensorsFlagState);
  }
};

const GlobalAutomaterializationRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Auto-materialize');
  return (
    <Page>
      <OverviewPageHeader tab="amp" />
      <GlobalAutomaterializationContent />
    </Page>
  );
};
