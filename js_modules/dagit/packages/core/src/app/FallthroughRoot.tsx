import React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {Box} from '../ui/Box';
import {ExternalAnchorButton} from '../ui/Button';
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
          const {allRepos, loading, locationEntries} = context;

          if (loading) {
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

          // If we have location entries but no repos, we have no useful objects to show.
          // Redirect to Workspace overview to surface relevant errors to the user.
          if (!allRepos.length && locationEntries.length) {
            return <Redirect to="/workspace" />;
          }

          // Default to the first job available in the first repo. This is kind of a legacy
          // approach, and might be worth rethinking.
          const firstRepo = allRepos[0] || null;
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
                    title={firstRepo ? 'No pipelines or jobs' : 'No repositories'}
                    description={
                      firstRepo
                        ? 'Your repository is loaded but no pipelines or jobs were found.'
                        : 'Add a repository to get started.'
                    }
                    action={
                      <ExternalAnchorButton href="https://docs.dagster.io/getting-started">
                        View documentation
                      </ExternalAnchorButton>
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
