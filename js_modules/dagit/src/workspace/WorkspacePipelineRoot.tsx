import * as React from 'react';
import {RouteComponentProps} from 'react-router-dom';

import {explorerPathFromString} from 'src/PipelinePathUtils';
import {WorkspacePipelineDisambiguationRoot} from 'src/workspace/WorkspacePipelineDisambiguationRoot';

type PathParams = {
  pipelinePath: string;
};

export const WorkspacePipelineRoot: React.FunctionComponent<RouteComponentProps<PathParams>> = (
  props: RouteComponentProps<PathParams>,
) => {
  const {match} = props;
  const {params} = match;
  const {pipelinePath} = params;
  const {pipelineName} = explorerPathFromString(pipelinePath);

  // [todo dish]: Redirect to appropriate repo pipeline based on the snapshot ID.
  // if (snapshotId) {
  //   return (
  //     <WorkspaceSnapshotDisambiguationRoot pipelineName={pipelineName} snapshotId={snapshotId} />
  //   );
  // }

  return <WorkspacePipelineDisambiguationRoot pipelineName={pipelineName} />;
};
