import {ErrorBoundary, MainContent} from '@dagster-io/ui-components';
import {Suspense, lazy, memo, useEffect, useRef} from 'react';
import {Route, Switch, useLocation} from 'react-router-dom';

import {AssetFeatureProvider} from '../assets/AssetFeatureContext';

const WorkspaceRoot = lazy(() => import('../workspace/WorkspaceRoot'));
const OverviewRoot = lazy(() => import('../overview/OverviewRoot'));
const AutomationRoot = lazy(() => import('../automation/AutomationRoot'));
const FallthroughRoot = lazy(() => import('./FallthroughRoot'));
const AssetsCatalogRoot = lazy(() => import('../assets/AssetsCatalogRoot'));
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
            <Suspense fallback={<div />}>
              <AssetsGroupsGlobalGraphRoot />
            </Suspense>
          </Route>
          <Route path="/assets(/?.*)">
            <Suspense fallback={<div />}>
              <AssetFeatureProvider>
                <AssetsCatalogRoot />
              </AssetFeatureProvider>
            </Suspense>
          </Route>
          <Route path="/runs" exact>
            <Suspense fallback={<div />}>
              <RunsRoot />
            </Suspense>
          </Route>
          <Route path="/runs/scheduled" exact>
            <Suspense fallback={<div />}>
              <ScheduledRunListRoot />
            </Suspense>
          </Route>
          <Route path="/runs/:runId" exact>
            <Suspense fallback={<div />}>
              <RunRoot />
            </Suspense>
          </Route>
          <Route path="/snapshots/:pipelinePath/:tab?">
            <Suspense fallback={<div />}>
              <SnapshotRoot />
            </Suspense>
          </Route>
          <Route path="/health">
            <Suspense fallback={<div />}>
              <InstanceHealthPage />
            </Suspense>
          </Route>
          <Route path="/concurrency">
            <Suspense fallback={<div />}>
              <InstanceConcurrencyPage />
            </Suspense>
          </Route>
          <Route path="/config">
            <Suspense fallback={<div />}>
              <InstanceConfig />
            </Suspense>
          </Route>
          <Route path="/locations" exact>
            <Suspense fallback={<div />}>
              <CodeLocationsPage />
            </Suspense>
          </Route>
          <Route path="/locations">
            <Suspense fallback={<div />}>
              <WorkspaceRoot />
            </Suspense>
          </Route>
          <Route path="/guess/:jobPath">
            <Suspense fallback={<div />}>
              <GuessJobLocationRoot />
            </Suspense>
          </Route>
          <Route path="/overview">
            <Suspense fallback={<div />}>
              <OverviewRoot />
            </Suspense>
          </Route>
          <Route path="/automation">
            <Suspense fallback={<div />}>
              <AutomationRoot />
            </Suspense>
          </Route>
          <Route path="/settings">
            <Suspense fallback={<div />}>
              <SettingsRoot />
            </Suspense>
          </Route>
          <Route path="*">
            <Suspense fallback={<div />}>
              <FallthroughRoot />
            </Suspense>
          </Route>
        </Switch>
      </ErrorBoundary>
    </MainContent>
  );
});
