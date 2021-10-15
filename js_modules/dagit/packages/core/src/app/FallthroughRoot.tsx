import React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {Box} from '../ui/Box';
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
                to={workspacePipelinePath({
                  repoName: firstRepo.repository.name,
                  repoLocation: firstRepo.repositoryLocation.name,
                  pipelineName: first.name,
                  isJob: first.isJob,
                })}
              />
            );
          }
          return (
            <Route
              render={() => (
                <Box padding={{vertical: 64}}>
                  <NonIdealState icon="no-results" title="No pipelines" />
                </Box>
              )}
            />
          );
        }}
      </WorkspaceContext.Consumer>
    </Switch>
  );
};
