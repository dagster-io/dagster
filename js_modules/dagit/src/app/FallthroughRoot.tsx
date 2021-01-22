import {NonIdealState} from '@blueprintjs/core';
import React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {WorkspaceContext} from 'src/workspace/WorkspaceContext';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

const InstanceRedirect = (props: RouteComponentProps<any>) => {
  const {location} = props;
  const path = `${location.pathname}${location.search}`;
  return <Redirect to={`/instance${path}`} />;
};

export const FallthroughRoot = () => {
  return (
    <Switch>
      <Route path={['/runs/(.*)?', '/assets/(.*)?', '/scheduler']} component={InstanceRedirect} />
      <WorkspaceContext.Consumer>
        {(context) => {
          if (context?.activeRepo?.repo.repository.pipelines.length) {
            const repoAddress = context.activeRepo.address;
            return (
              <Redirect
                to={workspacePathFromAddress(
                  repoAddress,
                  `/pipelines/${context?.activeRepo?.repo.repository.pipelines[0].name}/`,
                )}
              />
            );
          }
          return <Route render={() => <NonIdealState title="No pipelines" />} />;
        }}
      </WorkspaceContext.Consumer>
    </Switch>
  );
};
