import * as React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {JobLaunchpad} from '../launchpad/LaunchpadRoot';
import {LaunchpadSetupFromRunRoot} from '../launchpad/LaunchpadSetupFromRunRoot';
import {LaunchpadSetupRoot} from '../launchpad/LaunchpadSetupRoot';
import {PipelineNav} from '../nav/PipelineNav';
import {PipelinePartitionsRoot} from '../partitions/PipelinePartitionsRoot';
import {RepoAddress} from '../workspace/types';

import {PipelineOrJobDisambiguationRoot} from './PipelineOrJobDisambiguationRoot';
import {PipelineOverviewRoot} from './PipelineOverviewRoot';
import {PipelineRunsRoot} from './PipelineRunsRoot';

interface Props {
  repoAddress: RepoAddress;
}

export const PipelineRoot: React.FC<Props> = (props) => {
  const {repoAddress} = props;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        minWidth: 0,
        width: '100%',
        height: '100%',
      }}
    >
      <PipelineNav repoAddress={repoAddress} />
      <Switch>
        <Route path="/workspace/:repoPath/pipeline_or_job/:pipelinePath/(/?.*)">
          <PipelineOrJobDisambiguationRoot repoAddress={repoAddress} />
        </Route>
        <Route
          path={[
            '/workspace/:repoPath/pipelines/:pipelinePath/playground/setup',
            '/workspace/:repoPath/jobs/:pipelinePath/playground/setup',
          ]}
        >
          <LaunchpadSetupRoot repoAddress={repoAddress} />
        </Route>
        <Route
          path={[
            '/workspace/:repoPath/pipelines/:pipelinePath/playground/setup-from-run/:runId',
            '/workspace/:repoPath/jobs/:pipelinePath/playground/setup-from-run/:runId',
          ]}
        >
          <LaunchpadSetupFromRunRoot repoAddress={repoAddress} />
        </Route>
        <Route
          path={[
            '/workspace/:repoPath/pipelines/:pipelinePath/playground',
            '/workspace/:repoPath/jobs/:pipelinePath/playground',
          ]}
        >
          <JobLaunchpad repoAddress={repoAddress} />
        </Route>
        <Route
          path={[
            '/workspace/:repoPath/pipelines/:pipelinePath/runs/:runId',
            '/workspace/:repoPath/jobs/:pipelinePath/runs/:runId',
          ]}
          render={(props: RouteComponentProps<{runId: string}>) => (
            <Redirect to={`/instance/runs/${props.match.params.runId}`} />
          )}
        />
        <Route
          path={[
            '/workspace/:repoPath/pipelines/:pipelinePath/runs',
            '/workspace/:repoPath/jobs/:pipelinePath/runs',
          ]}
        >
          <PipelineRunsRoot repoAddress={repoAddress} />
        </Route>
        <Route
          path={[
            '/workspace/:repoPath/pipelines/:pipelinePath/partitions',
            '/workspace/:repoPath/jobs/:pipelinePath/partitions',
          ]}
        >
          <PipelinePartitionsRoot repoAddress={repoAddress} />
        </Route>
        <Route
          path={[
            '/workspace/:repoPath/pipelines/:pipelinePath/overview',
            '/workspace/:repoPath/jobs/:pipelinePath/overview',
          ]}
          render={(props) => (
            <Redirect to={`/workspace/${props.match.url.replace(/\/overview$/i, '')}`} />
          )}
        />
        <Route path={['/workspace/:repoPath/pipelines/(/?.*)', '/workspace/:repoPath/jobs/(/?.*)']}>
          <PipelineOverviewRoot repoAddress={repoAddress} />
        </Route>
      </Switch>
    </div>
  );
};
