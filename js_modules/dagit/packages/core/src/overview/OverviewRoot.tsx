import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';

import {InstanceBackfills} from '../instance/InstanceBackfills';
import {BackfillPage} from '../instance/backfill/BackfillPage';

import {OverviewActivityRoot} from './OverviewActivityRoot';
import {OverviewJobsRoot} from './OverviewJobsRoot';
import {OverviewResourcesRoot} from './OverviewResourcesRoot';
import {OverviewSchedulesRoot} from './OverviewSchedulesRoot';
import {OverviewSensorsRoot} from './OverviewSensorsRoot';
import {OverviewTimelineRoot} from './OverviewTimelineRoot';
import {PageHeader, Heading, Box} from '@dagster-io/ui';
import {OverviewTabs} from './OverviewTabs';
import {useFeatureFlags} from '../app/Flags';

export const OverviewRoot = () => {
  const {flagOverviewAssetsTab} = useFeatureFlags();
  return (
    <Switch>
      {flagOverviewAssetsTab ? (
        <Route path="/overview/activity">
          <OverviewActivityRoot />
        </Route>
      ) : (
        <Route path="/overview/timeline">
          <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
            <OverviewTimelineRoot
              TabButton={() => null}
              Header={React.useCallback(
                ({
                  refreshState,
                }: {
                  refreshState: React.ComponentProps<typeof OverviewTabs>['refreshState'];
                }) => (
                  <PageHeader
                    title={<Heading>Overview</Heading>}
                    tabs={<OverviewTabs tab="timeline" refreshState={refreshState} />}
                  />
                ),
                [],
              )}
            />
          </Box>
        </Route>
      )}
      <Route path="/overview/jobs">
        <OverviewJobsRoot />
      </Route>
      <Route path="/overview/schedules">
        <OverviewSchedulesRoot />
      </Route>
      <Route path="/overview/sensors">
        <OverviewSensorsRoot />
      </Route>
      <Route path="/overview/backfills/:backfillId">
        <BackfillPage />
      </Route>
      <Route path="/overview/backfills" exact>
        <InstanceBackfills />
      </Route>
      <Route path="/overview/resources">
        <OverviewResourcesRoot />
      </Route>
      <Route
        path="*"
        render={() =>
          flagOverviewAssetsTab ? (
            <Redirect to="/overview/activity" />
          ) : (
            <Redirect to="/overview/timeline" />
          )
        }
      />
    </Switch>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default OverviewRoot;
