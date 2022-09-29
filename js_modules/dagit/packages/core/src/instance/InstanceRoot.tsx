import {MainContent} from '@dagster-io/ui';
import * as React from 'react';
import {Redirect, Route, Switch, useLocation} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {AssetsCatalogRoot} from '../assets/AssetsCatalogRoot';
import {AssetsGroupsGlobalGraphRoot} from '../assets/AssetsGroupsGlobalGraphRoot';
import {RunRoot} from '../runs/RunRoot';
import {RunTimelineRoot} from '../runs/RunTimelineRoot';
import {RunsRoot} from '../runs/RunsRoot';
import {ScheduledRunListRoot} from '../runs/ScheduledRunListRoot';
import {SnapshotRoot} from '../snapshots/SnapshotRoot';

import {InstanceStatusRoot} from './InstanceStatusRoot';

export const InstanceRoot = () => {
  const {pathname} = useLocation();
  const {flagNewWorkspace} = useFeatureFlags();
  const main = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    main.current?.scrollTo({top: 0});
  }, [pathname]);

  return (
    <MainContent ref={main}>
      <Switch>
        <Route path="/instance/asset-groups(/?.*)">
          <AssetsGroupsGlobalGraphRoot />
        </Route>
        <Route path="/instance/assets(/?.*)">
          <AssetsCatalogRoot />
        </Route>
        <Route path="/instance/runs" exact>
          <RunsRoot />
        </Route>
        {flagNewWorkspace ? (
          <Route path="/instance/runs/timeline" exact>
            <RunTimelineRoot />
          </Route>
        ) : null}
        <Route path="/instance/runs/scheduled" exact>
          <ScheduledRunListRoot />
        </Route>
        <Route path="/instance/runs/:runId" exact>
          <RunRoot />
        </Route>
        <Route path="/instance/snapshots/:pipelinePath/:tab?">
          <SnapshotRoot />
        </Route>
        <Route path="/instance/:tab">
          <InstanceStatusRoot />
        </Route>
        <Route
          path="*"
          render={() => (
            <Redirect to={flagNewWorkspace ? '/instance/code-locations' : '/instance/overview'} />
          )}
        />
      </Switch>
    </MainContent>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default InstanceRoot;
