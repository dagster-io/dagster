import {Box, Heading, JoinedButtons, PageHeader} from '@dagster-io/ui-components';
import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';

import {OverviewAssetsRoot} from './OverviewAssetsRoot';
import {OverviewTabs} from './OverviewTabs';
import {OverviewTimelineRoot} from './OverviewTimelineRoot';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {ActivatableButton} from '../runs/RunListTabs';

export const OverviewActivityRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Activity');

  const header = React.useCallback(
    ({refreshState}: {refreshState: React.ComponentProps<typeof OverviewTabs>['refreshState']}) => (
      <PageHeader
        title={<Heading>Overview</Heading>}
        tabs={<OverviewTabs tab="activity" refreshState={refreshState} />}
      />
    ),
    [],
  );

  const [defaultTab, setDefaultTab] = useStateWithStorage<'timeline' | 'assets'>(
    'overview-activity-tab',
    (json) => (['timeline', 'assets'].includes(json) ? json : 'timeline'),
  );

  const tabButton = React.useCallback(
    ({selected}: {selected: 'timeline' | 'assets'}) => {
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
    [defaultTab, setDefaultTab],
  );

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <Switch>
        <Route path="/overview/activity/assets">
          <OverviewAssetsRoot Header={header} TabButton={tabButton} />
        </Route>
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
