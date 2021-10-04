import React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {NonIdealState} from '../ui/NonIdealState';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {workspacePipelinePath} from '../workspace/workspacePath';

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
            const first = firstRepo.repository.pipelines[0];
            return (
              <Redirect
                to={workspacePipelinePath(
                  firstRepo.repository.name,
                  firstRepo.repositoryLocation.name,
                  first.name,
                  first.modes[0].name,
                )}
              />
            );
          }
          return <Route render={() => <NonIdealState icon="no-results" title="No pipelines" />} />;
        }}
      </WorkspaceContext.Consumer>
    </Switch>
  );
};
