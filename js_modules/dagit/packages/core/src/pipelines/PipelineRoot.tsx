import * as React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {usePermissions} from '../app/Permissions';
import {PipelineExecutionRoot} from '../execute/PipelineExecutionRoot';
import {PipelineExecutionSetupRoot} from '../execute/PipelineExecutionSetupRoot';
import {PipelineNav} from '../nav/PipelineNav';
import {PipelinePartitionsRoot} from '../partitions/PipelinePartitionsRoot';
import {RepoAddress} from '../workspace/types';

import {PipelineExplorerRegexRoot} from './PipelineExplorerRoot';
import {PipelineOverviewRoot} from './PipelineOverviewRoot';
import {useEnforceModeInPipelinePath} from './PipelinePathUtils';
import {PipelineRunsRoot} from './PipelineRunsRoot';

interface Props {
  repoAddress: RepoAddress;
}

export const PipelineRoot: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const {canLaunchPipelineExecution} = usePermissions();

  useEnforceModeInPipelinePath();

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
          render={(props: RouteComponentProps<{pipelinePath: string; repoPath: string}>) => {
            const {pipelinePath, repoPath} = props.match.params;
            if (!canLaunchPipelineExecution) {
              return <Redirect to={`/workspace/${repoPath}/pipelines/${pipelinePath}`} />;
            }
            return (
              <PipelineExecutionSetupRoot pipelinePath={pipelinePath} repoAddress={repoAddress} />
            );
          }}
        />
        <Route
          path="/workspace/:repoPath/pipelines/:pipelinePath/playground"
          render={(props: RouteComponentProps<{pipelinePath: string; repoPath: string}>) => {
            const {pipelinePath, repoPath} = props.match.params;
            if (!canLaunchPipelineExecution) {
              return <Redirect to={`/workspace/${repoPath}/pipelines/${pipelinePath}`} />;
            }
            return (
              <PipelineExecutionRoot
                pipelinePath={props.match.params.pipelinePath}
                repoAddress={repoAddress}
              />
            );
          }}
        />
        <Route
          path="/workspace/:repoPath/pipelines/:pipelinePath/runs/:runId"
          render={(props: RouteComponentProps<{runId: string}>) => (
            <Redirect to={`/instance/runs/${props.match.params.runId}`} />
          )}
        />
        <Route
          path="/workspace/:repoPath/pipelines/:pipelinePath/runs"
          render={(props: RouteComponentProps<{pipelinePath: string}>) => (
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
        <Route
          path="/workspace/:repoPath/pipelines/(/?.*)"
          render={(props: RouteComponentProps) => (
            <PipelineExplorerRegexRoot {...props} repoAddress={repoAddress} />
          )}
        />
      </Switch>
    </div>
  );
};
