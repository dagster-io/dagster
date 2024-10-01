import {Box, JoinedButtons} from '@dagster-io/ui-components';
import * as React from 'react';
import {Redirect, Switch} from 'react-router-dom';

import {OverviewAssetsRoot} from './OverviewAssetsRoot';
import {OverviewPageHeader} from './OverviewPageHeader';
import {OverviewTabs} from './OverviewTabs';
import {OverviewTimelineRoot} from './OverviewTimelineRoot';
import {Route} from '../app/Route';
import {AssetFeatureContext} from '../assets/AssetFeatureContext';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {ActivatableButton} from '../runs/RunListTabs';

export const OverviewActivityRoot = () => {
  useDocumentTitle('Overview | Activity');

  const header = React.useCallback(
    ({refreshState}: {refreshState: React.ComponentProps<typeof OverviewTabs>['refreshState']}) => (
      <OverviewPageHeader tab="activity" refreshState={refreshState} />
    ),
    [],
  );

  const [_defaultTab, setDefaultTab] = useStateWithStorage<'timeline' | 'assets'>(
    'overview-activity-tab',
    (json) => (['timeline', 'assets'].includes(json) ? json : 'timeline'),
  );

  const {enableAssetHealthOverviewPreview} = React.useContext(AssetFeatureContext);
  const defaultTab = enableAssetHealthOverviewPreview ? 'timeline' : _defaultTab;

  const tabButton = React.useCallback(
    ({selected}: {selected: 'timeline' | 'assets'}) => {
      if (enableAssetHealthOverviewPreview) {
        return null;
      }
      if (defaultTab !== selected) {
        setDefaultTab(selected);
      }
      return (
        <JoinedButtons>
          <ActivatableButton $active={selected === 'timeline'} to="/overview/activity/timeline">
            Timeline
          </ActivatableButton>
          <ActivatableButton $active={selected === 'assets'} to="/overview/activity/assets">
            Assets
          </ActivatableButton>
        </JoinedButtons>
      );
    },
    [defaultTab, setDefaultTab, enableAssetHealthOverviewPreview],
  );

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <Switch>
        {!enableAssetHealthOverviewPreview && (
          <Route path="/overview/activity/assets">
            <OverviewAssetsRoot Header={header} TabButton={tabButton} />
          </Route>
        )}
        <Route path="/overview/activity/timeline">
          <OverviewTimelineRoot Header={header} TabButton={tabButton} />
        </Route>
        <Route
          path="*"
          isNestingRoute
          render={React.useCallback(
            () =>
              defaultTab === 'timeline' ? (
                <Redirect to="/overview/activity/timeline" />
              ) : (
                <Redirect to="/overview/activity/assets" />
              ),
            [defaultTab],
          )}
        />
      </Switch>
    </Box>
  );
};
