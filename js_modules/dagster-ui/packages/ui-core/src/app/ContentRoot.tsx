import {ErrorBoundary, MainContent} from '@dagster-io/ui-components';
import {memo, useEffect, useRef} from 'react';
import {Switch, useLocation} from 'react-router-dom';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import {AssetsOverviewRoot} from 'shared/assets/AssetsOverviewRoot.oss';

import {featureEnabled} from './Flags';
import {Route} from './Route';
import {AssetFeatureProvider} from '../assets/AssetFeatureContext';
import {RunsFeedBackfillPage} from '../instance/backfill/RunsFeedBackfillPage';
import RunsFeedRoot from '../runs/RunsFeedRoot';
import {lazy} from '../util/lazy';

const WorkspaceRoot = lazy(() => import('../workspace/WorkspaceRoot'));
const OverviewRoot = lazy(() => import('../overview/OverviewRoot'));
const MergedAutomationRoot = lazy(() => import('../automation/MergedAutomationRoot'));
const FallthroughRoot = lazy(() =>
  import('shared/app/FallthroughRoot.oss').then((mod) => ({default: mod.FallthroughRoot})),
);
const AssetsGlobalGraphRoot = lazy(() => import('../assets/AssetsGlobalGraphRoot'));
const CodeLocationsPage = lazy(() => import('../instance/CodeLocationsPage'));
const InstanceConfig = lazy(() => import('../instance/InstanceConfig'));
const InstanceConcurrencyPage = lazy(() => import('../instance/InstanceConcurrency'));
const InstanceHealthPage = lazy(() => import('../instance/InstanceHealthPage'));
const RunRoot = lazy(() => import('../runs/RunRoot'));
const RunsRoot = lazy(() => import('../runs/RunsRoot'));
const ScheduledRunListRoot = lazy(() => import('../runs/ScheduledRunListRoot'));
const SnapshotRoot = lazy(() => import('../snapshots/SnapshotRoot'));
const GuessJobLocationRoot = lazy(() => import('../workspace/GuessJobLocationRoot'));
const SettingsRoot = lazy(() => import('../settings/SettingsRoot'));
const JobsRoot = lazy(() => import('../jobs/JobsRoot'));

export const ContentRoot = memo(() => {
  const {pathname} = useLocation();
  const main = useRef<HTMLDivElement>(null);

  useEffect(() => {
    main.current?.scrollTo({top: 0});
  }, [pathname]);

  return (
    <MainContent ref={main}>
      <ErrorBoundary region="page" resetErrorOnChange={[pathname]}>
        <Switch>
          <Route path="/asset-groups(/?.*)">
            <AssetsGlobalGraphRoot />
          </Route>
          <Route path="/assets(/?.*)">
            <AssetFeatureProvider>
              <AssetsOverviewRoot
                headerBreadcrumbs={[{text: 'Assets', href: '/assets'}]}
                documentTitlePrefix="Assets"
              />
            </AssetFeatureProvider>
          </Route>
          {featureEnabled(FeatureFlag.flagLegacyRunsPage)
            ? // This is somewhat hacky but the Routes can't be wrapped by a fragment otherwise the Switch statement
              // stops working
              [
                <Route path="/runs-feed/b/:backfillId" key="3">
                  <RunsFeedBackfillPage />
                </Route>,
                <Route path={['/runs-feed', '/runs-feed/scheduled']} exact key="4">
                  <RunsFeedRoot />
                </Route>,
                <Route path="/runs" exact key="5">
                  <RunsRoot />
                </Route>,
                <Route path="/runs/scheduled" exact key="6">
                  <ScheduledRunListRoot />
                </Route>,
              ]
            : [
                <Route path="/runs/b/:backfillId" key="1">
                  <RunsFeedBackfillPage />
                </Route>,
                <Route path={['/runs', '/runs/scheduled']} exact key="2">
                  <RunsFeedRoot />
                </Route>,
              ]}
          <Route path="/runs/:runId" exact>
            <RunRoot />
          </Route>
          <Route path="/snapshots/:pipelinePath/:tab?">
            <SnapshotRoot />
          </Route>
          <Route path="/health">
            <InstanceHealthPage />
          </Route>
          <Route path="/concurrency">
            <InstanceConcurrencyPage />
          </Route>
          <Route path="/config">
            <InstanceConfig />
          </Route>
          <Route path="/locations" exact>
            <CodeLocationsPage />
          </Route>
          <Route path="/locations">
            <WorkspaceRoot />
          </Route>
          <Route path="/guess/:jobPath">
            <GuessJobLocationRoot />
          </Route>
          <Route path="/overview">
            <OverviewRoot />
          </Route>
          <Route path="/jobs">
            <JobsRoot />
          </Route>
          <Route path="/automation">
            <MergedAutomationRoot />
          </Route>
          <Route path="/deployment">
            <SettingsRoot />
          </Route>
          <Route path="*" isNestingRoute>
            <FallthroughRoot />
          </Route>
        </Switch>
      </ErrorBoundary>
    </MainContent>
  );
});
