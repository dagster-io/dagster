import * as React from 'react';
import {Route, Switch} from 'react-router-dom';

import {useActivePipelineForName} from 'src/DagsterRepositoryContext';
import {PipelineExplorerRoot} from 'src/PipelineExplorerRoot';
import {explorerPathFromString} from 'src/PipelinePathUtils';
import {PipelineRunsRoot} from 'src/PipelineRunsRoot';
import {PipelineExecutionRoot} from 'src/execute/PipelineExecutionRoot';
import {PipelineExecutionSetupRoot} from 'src/execute/PipelineExecutionSetupRoot';
import {PipelineNav} from 'src/nav/PipelineNav';
import {PipelinePartitionsRoot} from 'src/partitions/PipelinePartitionsRoot';
import {PipelineOverviewRoot} from 'src/pipelines/PipelineOverviewRoot';
import {RunRoot} from 'src/runs/RunRoot';

export const PipelineRoot: React.FunctionComponent<any> = (props: any) => {
  const {params} = props.match;
  const path = params['0'];
  const {pipelineName, snapshotId} = explorerPathFromString(path);
  const currentPipelineState = useActivePipelineForName(pipelineName);

  const isSnapshot = !!snapshotId;
  const isHistorical = isSnapshot && currentPipelineState?.pipelineSnapshotId !== snapshotId;

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
      <PipelineNav isHistorical={isHistorical} isSnapshot={isSnapshot} />
      <Switch>
        <Route path="/pipeline/:pipelinePath/overview" component={PipelineOverviewRoot} />
        <Route
          path="/pipeline/:pipelinePath/playground/setup"
          component={PipelineExecutionSetupRoot}
        />
        <Route path="/pipeline/:pipelinePath/playground" component={PipelineExecutionRoot} />
        <Route path="/pipeline/:pipelinePath/runs/:runId" component={RunRoot} />
        <Route path="/pipeline/:pipelinePath/runs" component={PipelineRunsRoot} />
        <Route path="/pipeline/:pipelinePath/partitions" component={PipelinePartitionsRoot} />
        {/* Capture solid subpath in a regex match */}
        <Route path="/pipeline/(/?.*)" component={PipelineExplorerRoot} />
      </Switch>
    </div>
  );
};
