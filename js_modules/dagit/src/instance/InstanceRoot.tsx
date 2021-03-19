import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';

import {AssetEntryRoot} from '../assets/AssetEntryRoot';
import {AssetsCatalogRoot} from '../assets/AssetsCatalogRoot';
import {RunRoot} from '../runs/RunRoot';
import {RunsRoot} from '../runs/RunsRoot';
import {SnapshotRoot} from '../snapshots/SnapshotRoot';
import {MainContent} from '../ui/MainContent';

import {InstanceStatusRoot} from './InstanceStatusRoot';

export const InstanceRoot = () => {
  return (
    <MainContent>
      <Switch>
        <Route path="/instance/assets" exact component={AssetsCatalogRoot} />
        <Route path="/instance/assets/(/?.*)" component={AssetEntryRoot} />
        <Route path="/instance/runs" exact component={RunsRoot} />
        <Route path="/instance/runs/:runId" exact component={RunRoot} />
        <Route path="/instance/snapshots/:pipelinePath/:tab?" component={SnapshotRoot} />
        <Route
          path="/instance/:tab"
          render={({match}) => <InstanceStatusRoot tab={match.params.tab} />}
        />
        <Route path="/instance" render={() => <Redirect to="/instance/health" />} />
      </Switch>
    </MainContent>
  );
};
