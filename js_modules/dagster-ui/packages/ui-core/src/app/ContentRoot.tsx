import {ErrorBoundary, MainContent} from '@dagster-io/ui-components';
import {lazy, memo, useEffect, useRef} from 'react';
import {Route, Switch, useLocation} from 'react-router-dom';

import {TrackedSuspense} from './TrackedSuspense';
import {AssetFeatureProvider} from '../assets/AssetFeatureContext';
import {AssetsOverview} from '../assets/AssetsOverview';

const WorkspaceRoot = lazy(() => import('../workspace/WorkspaceRoot'));
const OverviewRoot = lazy(() => import('../overview/OverviewRoot'));
const AutomationRoot = lazy(() => import('../automation/AutomationRoot'));
const FallthroughRoot = lazy(() => import('./FallthroughRoot'));
const AssetsGroupsGlobalGraphRoot = lazy(() => import('../assets/AssetsGroupsGlobalGraphRoot'));
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
            <TrackedSuspense fallback={<div />} id={id('asset-groups')}>
              <AssetsGroupsGlobalGraphRoot />
            </TrackedSuspense>
          </Route>
          <Route path="/assets(/?.*)">
            <TrackedSuspense fallback={<div />} id={id('assets')}>
              <AssetFeatureProvider>
                <AssetsOverview
                  headerBreadcrumbs={[{text: 'Assets', href: '/assets'}]}
                  documentTitlePrefix="Assets"
                />
              </AssetFeatureProvider>
            </TrackedSuspense>
          </Route>
          <Route path="/runs" exact>
            <TrackedSuspense fallback={<div />} id={id('runs')}>
              <RunsRoot />
            </TrackedSuspense>
          </Route>
          <Route path="/runs/scheduled" exact>
            <TrackedSuspense fallback={<div />} id={id('runs/scheduled')}>
              <ScheduledRunListRoot />
            </TrackedSuspense>
          </Route>
          <Route path="/runs/:runId" exact>
            <TrackedSuspense fallback={<div />} id={id('runs/:runId')}>
              <RunRoot />
            </TrackedSuspense>
          </Route>
          <Route path="/snapshots/:pipelinePath/:tab?">
            <TrackedSuspense fallback={<div />} id={id('snapshots')}>
              <SnapshotRoot />
            </TrackedSuspense>
          </Route>
          <Route path="/health">
            <TrackedSuspense fallback={<div />} id={id('health')}>
              <InstanceHealthPage />
            </TrackedSuspense>
          </Route>
          <Route path="/concurrency">
            <TrackedSuspense fallback={<div />} id={id('concurrency')}>
              <InstanceConcurrencyPage />
            </TrackedSuspense>
          </Route>
          <Route path="/config">
            <TrackedSuspense fallback={<div />} id={id('config')}>
              <InstanceConfig />
            </TrackedSuspense>
          </Route>
          <Route path="/locations" exact>
            <TrackedSuspense fallback={<div />} id={id('"locations"')}>
              <CodeLocationsPage />
            </TrackedSuspense>
          </Route>
          <Route path="/locations">
            <TrackedSuspense fallback={<div />} id={id('locations')}>
              <WorkspaceRoot />
            </TrackedSuspense>
          </Route>
          <Route path="/guess/:jobPath">
            <TrackedSuspense fallback={<div />} id={id('guess/:jobPath')}>
              <GuessJobLocationRoot />
            </TrackedSuspense>
          </Route>
          <Route path="/overview">
            <TrackedSuspense id={id('Overview')} fallback={<div />}>
              <OverviewRoot />
            </TrackedSuspense>
          </Route>
          <Route path="/jobs">
            <TrackedSuspense id={id('JobsRoot')} fallback={<div />}>
              <JobsRoot />
            </TrackedSuspense>
          </Route>
          <Route path="/automation">
            <TrackedSuspense fallback={<div />} id={id('automation')}>
              <AutomationRoot />
            </TrackedSuspense>
          </Route>
          <Route path="/settings">
            <TrackedSuspense fallback={<div />} id={id('settings')}>
              <SettingsRoot />
            </TrackedSuspense>
          </Route>
          <Route path="*">
            <TrackedSuspense fallback={<div />} id={id('*')}>
              <FallthroughRoot />
            </TrackedSuspense>
          </Route>
        </Switch>
      </ErrorBoundary>
    </MainContent>
  );
});

function id(str: string) {
  return `ContentRoot:${str}`;
}
