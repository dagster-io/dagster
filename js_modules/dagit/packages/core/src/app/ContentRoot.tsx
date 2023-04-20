import {MainContent, ErrorBoundary} from '@dagster-io/ui';
import * as React from 'react';
import {Route, Switch, useLocation} from 'react-router-dom';

const WorkspaceRoot = React.lazy(() => import('../workspace/WorkspaceRoot'));
const OverviewRoot = React.lazy(() => import('../overview/OverviewRoot'));
const FallthroughRoot = React.lazy(() => import('./FallthroughRoot'));
const AssetsCatalogRoot = React.lazy(() => import('../assets/AssetsCatalogRoot'));
const AssetsGroupsGlobalGraphRoot = React.lazy(
  () => import('../assets/AssetsGroupsGlobalGraphRoot'),
);
const CodeLocationsPage = React.lazy(() => import('../instance/CodeLocationsPage'));
const InstanceConfig = React.lazy(() => import('../instance/InstanceConfig'));
const InstanceHealthPage = React.lazy(() => import('../instance/InstanceHealthPage'));
const RunRoot = React.lazy(() => import('../runs/RunRoot'));
const RunsRoot = React.lazy(() => import('../runs/RunsRoot'));
const ScheduledRunListRoot = React.lazy(() => import('../runs/ScheduledRunListRoot'));
const SnapshotRoot = React.lazy(() => import('../snapshots/SnapshotRoot'));
const GuessJobLocationRoot = React.lazy(() => import('../workspace/GuessJobLocationRoot'));

export const ContentRoot = React.memo(() => {
  const {pathname} = useLocation();
  const main = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    main.current?.scrollTo({top: 0});
  }, [pathname]);

  return (
    <MainContent ref={main}>
      <ErrorBoundary region="page" resetErrorOnChange={[pathname]}>
        <Switch>
          <Route path="/asset-groups(/?.*)">
            <React.Suspense fallback={<div />}>
              <AssetsGroupsGlobalGraphRoot />
            </React.Suspense>
          </Route>
          <Route path="/assets(/?.*)">
            <React.Suspense fallback={<div />}>
              <AssetsCatalogRoot />
            </React.Suspense>
          </Route>
          <Route path="/runs" exact>
            <React.Suspense fallback={<div />}>
              <RunsRoot />
            </React.Suspense>
          </Route>
          <Route path="/runs/scheduled" exact>
            <React.Suspense fallback={<div />}>
              <ScheduledRunListRoot />
            </React.Suspense>
          </Route>
          <Route path="/runs/:runId" exact>
            <React.Suspense fallback={<div />}>
              <RunRoot />
            </React.Suspense>
          </Route>
          <Route path="/snapshots/:pipelinePath/:tab?">
            <React.Suspense fallback={<div />}>
              <SnapshotRoot />
            </React.Suspense>
          </Route>
          <Route path="/health">
            <React.Suspense fallback={<div />}>
              <InstanceHealthPage />
            </React.Suspense>
          </Route>
          <Route path="/config">
            <React.Suspense fallback={<div />}>
              <InstanceConfig />
            </React.Suspense>
          </Route>
          <Route path="/locations" exact>
            <React.Suspense fallback={<div />}>
              <CodeLocationsPage />
            </React.Suspense>
          </Route>
          <Route path="/locations">
            <React.Suspense fallback={<div />}>
              <WorkspaceRoot />
            </React.Suspense>
          </Route>
          <Route path="/guess/:jobPath">
            <React.Suspense fallback={<div />}>
              <GuessJobLocationRoot />
            </React.Suspense>
          </Route>
          <Route path="/overview">
            <React.Suspense fallback={<div />}>
              <OverviewRoot />
            </React.Suspense>
          </Route>
          <Route path="*">
            <React.Suspense fallback={<div />}>
              <FallthroughRoot />
            </React.Suspense>
          </Route>
        </Switch>
      </ErrorBoundary>
    </MainContent>
  );
});
