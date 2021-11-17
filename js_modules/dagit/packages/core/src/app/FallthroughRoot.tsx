import React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {NonIdealState} from '../ui/NonIdealState';
import {Spinner} from '../ui/Spinner';
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

          if (context.loading) {
            return (
              <Route
                render={() => (
                  <Box
                    flex={{direction: 'row', justifyContent: 'center'}}
                    style={{paddingTop: '100px'}}
                  >
                    <Box flex={{direction: 'row', alignItems: 'center', gap: 16}}>
                      <Spinner purpose="section" />
                      <div style={{color: ColorsWIP.Gray600}}>Loading workspace…</div>
                    </Box>
                  </Box>
                )}
              />
            );
          }

          return (
            <Route
              render={() => (
                <Box padding={{vertical: 64}}>
                  <NonIdealState
                    icon="no-results"
                    title={firstRepo ? 'No pipelines or jobs' : 'No repositories'}
                    description={
                      firstRepo
                        ? 'Your repository is loaded but no pipelines or jobs were found.'
                        : 'Add a repository to get started.'
                    }
                    action={
                      <a
                        href="https://docs.dagster.io/getting-started"
                        target="_blank"
                        rel="nofollow noreferrer"
                      >
                        View documentation
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
