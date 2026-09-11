import {MockedProvider} from '@apollo/client/testing';
import {FeatureFlag} from '@shared/FeatureFlags';
import {MainNavigation} from '@shared/app/navigation/MainNavigation';
import {useContext} from 'react';

import {AppContext, AppContextValue} from '../../AppContext';
import {NavCollapseContext, NavCollapseProvider} from '../NavCollapseProvider';
import {getBottomGroups, getTopGroups} from '../mainNavigationItems';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'MainNavigation',
  component: MainNavigation,
};

const config = {
  featureFlags: {} as Record<FeatureFlag, boolean>,
  jobState: 'has-jobs' as const,
};

const Nav = () => {
  const {isCollapsed} = useContext(NavCollapseContext);
  return (
    <div style={{width: isCollapsed ? 68 : 240, height: 700}}>
      <MainNavigation
        collapsed={isCollapsed}
        topGroups={getTopGroups(config)}
        bottomGroups={getBottomGroups(config)}
      />
    </div>
  );
};

export const Default = () => {
  return (
    <MockedProvider mocks={[]}>
      <NavCollapseProvider>
        <Nav />
      </NavCollapseProvider>
    </MockedProvider>
  );
};

const labelled: AppContextValue = {
  basePath: '',
  rootServerURI: '',
  telemetryEnabled: false,
  uiLabel: 'Production',
  uiIntent: 'danger',
};

export const WithDeploymentLabel = () => {
  return (
    <AppContext.Provider value={labelled}>
      <MockedProvider mocks={[]}>
        <NavCollapseProvider>
          <Nav />
        </NavCollapseProvider>
      </MockedProvider>
    </AppContext.Provider>
  );
};
