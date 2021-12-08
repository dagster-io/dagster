import * as React from 'react';
import {Redirect, Route, Switch, useLocation} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {AssetEntryRoot} from '../assets/AssetEntryRoot';
import {AssetsCatalogRoot} from '../assets/AssetsCatalogRoot';
import {RunRoot} from '../runs/RunRoot';
import {RunsRoot} from '../runs/RunsRoot';
import {SnapshotRoot} from '../snapshots/SnapshotRoot';
import {MainContent} from '../ui/MainContent';

import {InstanceStatusRoot} from './InstanceStatusRoot';

export const InstanceRoot = () => {
  const {pathname} = useLocation();
  const {flagInstanceOverview} = useFeatureFlags();
  const main = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    main.current?.scrollTo({top: 0});
  }, [pathname]);

  return (
    <MainContent ref={main}>
      <Switch>
        <Route path="/instance/assets" exact component={AssetsCatalogRoot} />
        <Route path="/instance/assets/(/?.*)" component={AssetEntryRoot} />
        <Route path="/instance/runs" exact component={RunsRoot} />
        <Route path="/instance/runs/:runId" exact component={RunRoot} />
        <Route path="/instance/snapshots/:pipelinePath/:tab?" component={SnapshotRoot} />
        <Route path="/instance/:tab" component={InstanceStatusRoot} />
        <Route
          path="*"
          render={() => (
            <Redirect to={flagInstanceOverview ? '/instance/overview' : '/instance/health'} />
          )}
        />
      </Switch>
    </MainContent>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default InstanceRoot;
