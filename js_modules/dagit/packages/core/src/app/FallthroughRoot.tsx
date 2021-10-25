import React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
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
                  <NonIdealState
                    icon="no-results"
                    title={"No code locations defined"}
                    description={
                      "No user code locations are configured for this deployment. For instructions on setting up this deployment, view the Cloud docs."
                    }
                    action={
                      <a
                        href="https://docs.dagster.cloud/"
                        target="_blank"
                        rel="noreferrer"
                      >
                        <ButtonWIP>View Cloud Documentation</ButtonWIP>
                      </a>
                    }
                  />
                </Box>
              )}
            />
          );
        }}
      </WorkspaceContext.Consumer>
    </Switch>
  );
};
