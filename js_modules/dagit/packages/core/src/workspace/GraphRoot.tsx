import React from 'react';
import {Link, RouteComponentProps} from 'react-router-dom';

import {RepositoryLink} from '../nav/RepositoryLink';
import {PipelineExplorerRegexRoot} from '../pipelines/PipelineExplorerRoot';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {PageHeader} from '../ui/PageHeader';
import {Heading} from '../ui/Text';

import {RepoAddress} from './types';
import {workspacePathFromAddress} from './workspacePath';

interface Props extends RouteComponentProps {
  repoAddress: RepoAddress;
}

export const GraphRoot: React.FC<Props> = (props) => {
  const {repoAddress} = props;
  const path = explorerPathFromString(props.match.params[0]);

  // Show the name of the composite solid we are within (-1 is the selection, -2 is current parent)
  // or the name of the pipeline tweaked to look a bit more like a graph name.
  const title =
    path.pathSolids.length > 1 ? path.pathSolids[path.pathSolids.length - 2] : path.pipelineName;

  return (
    <div style={{height: '100%', display: 'flex', flexDirection: 'column'}}>
      <div style={{padding: 20, borderBottom: '1px solid #ccc'}}>
        <PageHeader
          title={<Heading>{title}</Heading>}
          description={
            <>
              <Link to={workspacePathFromAddress(repoAddress, '/graphs')}>Graph</Link> in{' '}
              <RepositoryLink repoAddress={repoAddress} />
            </>
          }
          icon="diagram-tree"
        />
      </div>
      <div style={{position: 'relative', minHeight: 0, flex: 1, display: 'flex'}}>
        <PipelineExplorerRegexRoot {...props} repoAddress={repoAddress} pageContext="graph" />
      </div>
    </div>
  );
};
