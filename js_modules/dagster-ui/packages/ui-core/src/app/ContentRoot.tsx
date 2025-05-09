import {ErrorBoundary, MainContent} from '@dagster-io/ui-components';
import {memo, useEffect, useRef} from 'react';
import {Redirect, Switch, useLocation} from 'react-router-dom';
import {AssetsOverviewRoot} from 'shared/assets/AssetsOverviewRoot.oss';

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
const InstanceConfig = lazy(() => import('../instance/InstanceConfig'));
const InstanceConcurrencyPage = lazy(() => import('../instance/InstanceConcurrency'));
const InstanceHealthPage = lazy(() => import('../instance/InstanceHealthPage'));
const RunRoot = lazy(() => import('../runs/RunRoot'));
const SnapshotRoot = lazy(() => import('../snapshots/SnapshotRoot'));
const GuessJobLocationRoot = lazy(() => import('../workspace/GuessJobLocationRoot'));
const SettingsRoot = lazy(() => import('../settings/SettingsRoot'));
const JobsRoot = lazy(() => import('../jobs/JobsRoot'));
const IntegrationsRoot = lazy(() => import('../integrations/IntegrationsRoot'));

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
          <Route path="/runs/b/:backfillId" key="1">
            <RunsFeedBackfillPage />
          </Route>
          ,
          <Route path={['/runs', '/runs/scheduled', '/backfills']} exact key="2">
            <RunsFeedRoot />
          </Route>
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
            <Redirect to="/deployment/locations" />
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
          <Route path="/integrations">
            <IntegrationsRoot />
          </Route>
          <Route path="*" isNestingRoute>
            <FallthroughRoot />
          </Route>
        </Switch>
      </ErrorBoundary>
    </MainContent>
  );
});
