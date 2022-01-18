import * as React from 'react';
import {Route, Switch, useParams} from 'react-router-dom';

import {PipelineExplorerSnapshotRoot} from '../pipelines/PipelineExplorerRoot';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {PipelineRunsRoot} from '../pipelines/PipelineRunsRoot';

import {SnapshotNav} from './SnapshotNav';

export const SnapshotRoot = () => {
  const {pipelinePath, tab} = useParams<{
    pipelinePath: string;
    tab?: string;
  }>();
  const explorerPath = explorerPathFromString(pipelinePath);

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
      <SnapshotNav activeTab={tab} explorerPath={explorerPath} />
      <Switch>
        <Route path="/instance/snapshots/:pipelinePath/runs">
          <PipelineRunsRoot />
        </Route>
        <Route path="/instance/snapshots/(/?.*)">
          <PipelineExplorerSnapshotRoot />
        </Route>
      </Switch>
    </div>
  );
};
