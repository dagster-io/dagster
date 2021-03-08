import {NonIdealState} from '@blueprintjs/core';
import React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {WorkspaceContext} from 'src/workspace/WorkspaceContext';
import {workspacePath} from 'src/workspace/workspacePath';

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
          const firstRepo = context.allRepos[0] || null;
          if (firstRepo?.repository.pipelines.length) {
            return (
              <Redirect
                to={workspacePath(
                  firstRepo.repository.name,
                  firstRepo.repositoryLocation.name,
                  `/pipelines/${firstRepo.repository.pipelines[0].name}/`,
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
