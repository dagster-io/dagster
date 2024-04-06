import {Box, JoinedButtons} from '@dagster-io/ui-components';
import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';

import {OverviewAssetsRoot} from './OverviewAssetsRoot';
import {OverviewPageHeader} from './OverviewPageHeader';
import {OverviewTabs} from './OverviewTabs';
import {OverviewTimelineRoot} from './OverviewTimelineRoot';
import {useFeatureFlags} from '../app/Flags';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {ActivatableButton} from '../runs/RunListTabs';

export const OverviewActivityRoot = () => {
  useTrackPageView();
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

  const {flagUseNewAssetHealthOverviewPage} = useFeatureFlags();
  const defaultTab = flagUseNewAssetHealthOverviewPage ? 'timeline' : _defaultTab;

  const tabButton = React.useCallback(
    ({selected}: {selected: 'timeline' | 'assets'}) => {
      if (flagUseNewAssetHealthOverviewPage) {
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
    [defaultTab, setDefaultTab, flagUseNewAssetHealthOverviewPage],
  );

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <Switch>
        {!flagUseNewAssetHealthOverviewPage && (
          <Route path="/overview/activity/assets">
            <OverviewAssetsRoot Header={header} TabButton={tabButton} />
          </Route>
        )}
        <Route path="/overview/activity/timeline">
          <OverviewTimelineRoot Header={header} TabButton={tabButton} />
        </Route>
        <Route
          path="*"
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
