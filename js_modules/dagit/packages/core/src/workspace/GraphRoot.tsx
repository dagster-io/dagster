import React from 'react';
import {RouteComponentProps} from 'react-router-dom';

import {RepositoryLink} from '../nav/RepositoryLink';
import {PipelineExplorerRegexRoot} from '../pipelines/PipelineExplorerRoot';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {PageHeader} from '../ui/PageHeader';
import {TagWIP} from '../ui/TagWIP';
import {Heading} from '../ui/Text';

import {RepoAddress} from './types';

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
      <PageHeader
        title={<Heading>{title}</Heading>}
        tags={
          <TagWIP icon="schema">
            Graph in <RepositoryLink repoAddress={repoAddress} />
          </TagWIP>
        }
      />
      <Box border={{side: 'top', width: 1, color: ColorsWIP.KeylineGray}}>
        <div style={{minHeight: 0, flex: 1, display: 'flex'}}>
          <PipelineExplorerRegexRoot {...props} repoAddress={repoAddress} />
        </div>
      </Box>
    </div>
  );
};
