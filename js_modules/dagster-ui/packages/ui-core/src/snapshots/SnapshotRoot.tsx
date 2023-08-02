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
        <Route path="/snapshots/:pipelinePath/runs">
          <PipelineRunsRoot />
        </Route>
        <Route path="/snapshots/(/?.*)">
          <PipelineExplorerSnapshotRoot />
        </Route>
      </Switch>
    </div>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default SnapshotRoot;
