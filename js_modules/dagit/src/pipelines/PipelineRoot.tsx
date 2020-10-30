import * as React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {PipelineExplorerRegexRoot} from 'src/PipelineExplorerRoot';
import {PipelineRunsRoot} from 'src/PipelineRunsRoot';
import {PipelineExecutionRoot} from 'src/execute/PipelineExecutionRoot';
import {PipelineExecutionSetupRoot} from 'src/execute/PipelineExecutionSetupRoot';
import {PipelineNav} from 'src/nav/PipelineNav';
import {PipelinePartitionsRoot} from 'src/partitions/PipelinePartitionsRoot';
import {PipelineOverviewRoot} from 'src/pipelines/PipelineOverviewRoot';
import {RepoAddress} from 'src/workspace/types';

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
        <Route
          path="/workspace/:repoPath/pipelines/:pipelinePath/overview"
          render={(props) => <PipelineOverviewRoot {...props} repoAddress={repoAddress} />}
        />
        <Route
          path="/workspace/:repoPath/pipelines/:pipelinePath/playground/setup"
          component={(props: RouteComponentProps<{pipelinePath: string}>) => (
            <PipelineExecutionSetupRoot
              pipelinePath={props.match.params.pipelinePath}
              repoAddress={repoAddress}
            />
          )}
        />
        <Route
          path="/workspace/:repoPath/pipelines/:pipelinePath/playground"
          component={(props: RouteComponentProps<{pipelinePath: string}>) => (
            <PipelineExecutionRoot
              pipelinePath={props.match.params.pipelinePath}
              repoAddress={repoAddress}
            />
          )}
        />
        <Route
          path="/workspace/:repoPath/pipelines/:pipelinePath/runs/:runId"
          render={(props: RouteComponentProps<{runId: string}>) => (
            <Redirect to={`/instance/runs/${props.match.params.runId}`} />
          )}
        />
        {/* Move to `/instance`: */}
        <Route
          path="/workspace/:repoPath/pipelines/:pipelinePath/runs"
          component={(props: RouteComponentProps<{pipelinePath: string}>) => (
            <PipelineRunsRoot pipelinePath={props.match.params.pipelinePath} />
          )}
        />
        <Route
          path="/workspace/:repoPath/pipelines/:pipelinePath/partitions"
          render={(props: RouteComponentProps<{pipelinePath: string}>) => (
            <PipelinePartitionsRoot
              pipelinePath={props.match.params.pipelinePath}
              repoAddress={repoAddress}
            />
          )}
        />
        {/* Capture solid subpath in a regex match */}
        <Route path="/workspace/:repoPath/pipelines/(/?.*)" component={PipelineExplorerRegexRoot} />
      </Switch>
    </div>
  );
};
