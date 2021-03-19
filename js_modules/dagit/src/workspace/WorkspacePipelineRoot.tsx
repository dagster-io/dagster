import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Link, Redirect, useLocation, useRouteMatch} from 'react-router-dom';

import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {LoadingSpinner} from '../ui/Loading';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Table} from '../ui/Table';
import {Heading} from '../ui/Text';

import {optionToRepoAddress, useRepositoryOptions} from './WorkspaceContext';
import {findRepoContainingPipeline} from './findRepoContainingPipeline';
import {workspacePath, workspacePathFromAddress} from './workspacePath';

interface Props {
  pipelinePath: string;
}

export const WorkspacePipelineRoot: React.FC<Props> = (props) => {
  const {pipelinePath} = props;
  const entireMatch = useRouteMatch('/workspace/pipelines/(/?.*)');
  const location = useLocation();

  const toAppend = entireMatch!.params[0];
  const {search} = location;

  const {pipelineName} = explorerPathFromString(pipelinePath);
  const {loading, options} = useRepositoryOptions();

  if (loading) {
    return <LoadingSpinner purpose="page" />;
  }

  const reposWithMatch = findRepoContainingPipeline(options, pipelineName);
  if (reposWithMatch.length === 0) {
    return (
      <NonIdealState
        icon="cube"
        title="No matching pipelines"
        description={
          <div>
            <div>
              <strong>{pipelineName}</strong>
            </div>
            was not found in any repositories in this workspace.
          </div>
        }
      />
    );
  }

  if (reposWithMatch.length === 1) {
    const repoAddress = optionToRepoAddress(reposWithMatch[0]);
    const to = workspacePathFromAddress(repoAddress, `/pipelines/${toAppend}${search}`);
    return <Redirect to={to} />;
  }

  return (
    <Page>
      <PageHeader
        title={<Heading>{pipelineName}</Heading>}
        icon="diagram-tree"
        description="Pipeline in multiple repositories"
      />
      <Box margin={{vertical: 20}}>
        <Alert
          intent="info"
          title={
            <div>
              Pipelines named <strong>{pipelineName}</strong> were found in multiple repositories.
            </div>
          }
        />
      </Box>
      <Table>
        <thead>
          <tr>
            <th>Repository name and location</th>
            <th>Pipeline</th>
          </tr>
        </thead>
        <tbody>
          {reposWithMatch.map((repository) => {
            const {
              repository: {name},
              repositoryLocation: {name: location},
            } = repository;
            const repoString = `${name}@${location}`;
            return (
              <tr key={repoString}>
                <td style={{width: '40%'}}>{repoString}</td>
                <td>
                  <Link to={workspacePath(name, location, `/pipelines/${pipelineName}`)}>
                    {pipelineName}
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    </Page>
  );
};
