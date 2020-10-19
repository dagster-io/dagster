import * as React from 'react';
import {Redirect, Route, Switch} from 'react-router-dom';

import {AssetEntryRoot} from 'src/assets/AssetEntryRoot';
import {AssetsCatalogRoot} from 'src/assets/AssetsCatalogRoot';
import {InstanceDetailsRoot} from 'src/instance/InstanceDetailsRoot';
import {RunsRoot} from 'src/runs/RunsRoot';
import {SchedulerRoot} from 'src/schedules/SchedulerRoot';
import {MainContent} from 'src/ui/MainContent';

export const InstanceRoot: React.FunctionComponent<{}> = () => {
  return (
    <MainContent>
      <Switch>
        <Route path="/instance/details" component={InstanceDetailsRoot} />
        <Route path="/instance/assets" exact component={AssetsCatalogRoot} />
        <Route path="/instance/assets/(/?.*)" component={AssetEntryRoot} />
        <Route path="/instance/runs" exact component={RunsRoot} />
        <Route path="/instance/scheduler" exact component={SchedulerRoot} />
        <Route path="/instance/(.*)?" render={() => <Redirect to="/instance/details" />} />
      </Switch>
    </MainContent>
  );
};
