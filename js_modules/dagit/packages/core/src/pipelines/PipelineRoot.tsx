import * as React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {usePermissions} from '../app/Permissions';
import {PipelineExecutionRoot} from '../execute/PipelineExecutionRoot';
import {PipelineExecutionSetupRoot} from '../execute/PipelineExecutionSetupRoot';
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
  const {canLaunchPipelineExecution} = usePermissions();

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
          path="/workspace/:repoPath/pipeline_or_job/:pipelinePath"
          render={(props: RouteComponentProps<{repoPath: string; pipelinePath: string}>) => {
            return <PipelineOrJobDisambiguationRoot {...props} repoAddress={repoAddress} />;
          }}
        />
        <Route
          path={[
            '/workspace/:repoPath/pipelines/:pipelinePath/playground/setup',
            '/workspace/:repoPath/jobs/:pipelinePath/playground/setup',
          ]}
          render={(props: RouteComponentProps<{pipelinePath: string; repoPath: string}>) => {
            const {pipelinePath, repoPath} = props.match.params;
            if (!canLaunchPipelineExecution) {
              return <Redirect to={`/workspace/${repoPath}/pipeline_or_job/${pipelinePath}`} />;
            }
            return (
              <PipelineExecutionSetupRoot pipelinePath={pipelinePath} repoAddress={repoAddress} />
            );
          }}
        />
        <Route
          path={[
            '/workspace/:repoPath/pipelines/:pipelinePath/playground',
            '/workspace/:repoPath/jobs/:pipelinePath/playground',
          ]}
          render={(props: RouteComponentProps<{pipelinePath: string; repoPath: string}>) => {
            const {pipelinePath, repoPath} = props.match.params;
            if (!canLaunchPipelineExecution) {
              return <Redirect to={`/workspace/${repoPath}/pipeline_or_job/${pipelinePath}`} />;
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
          render={(props: RouteComponentProps<{pipelinePath: string}>) => (
            <PipelineRunsRoot
              pipelinePath={props.match.params.pipelinePath}
              repoAddress={repoAddress}
            />
          )}
        />
        <Route
          path={[
            '/workspace/:repoPath/pipelines/:pipelinePath/partitions',
            '/workspace/:repoPath/jobs/:pipelinePath/partitions',
          ]}
          render={(props: RouteComponentProps<{pipelinePath: string}>) => (
            <PipelinePartitionsRoot
              pipelinePath={props.match.params.pipelinePath}
              repoAddress={repoAddress}
            />
          )}
        />
        <Route
          path={[
            '/workspace/:repoPath/pipelines/:pipelinePath/overview',
            '/workspace/:repoPath/jobs/:pipelinePath/overview',
          ]}
          render={(props) => (
            <Redirect to={`/workspace/${props.match.url.replace(/\/overview$/i, '')}`} />
          )}
        />
        <Route
          path={['/workspace/:repoPath/pipelines/(/?.*)', '/workspace/:repoPath/jobs/(/?.*)']}
          render={(props: any) => <PipelineOverviewRoot {...props} repoAddress={repoAddress} />}
        />
      </Switch>
    </div>
  );
};
