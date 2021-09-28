import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Link, Redirect, useLocation, useRouteMatch} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {LoadingSpinner} from '../ui/Loading';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Table} from '../ui/Table';
import {Heading} from '../ui/Text';

import {optionToRepoAddress, useRepositoryOptions} from './WorkspaceContext';
import {buildRepoPath} from './buildRepoAddress';
import {findRepoContainingPipeline} from './findRepoContainingPipeline';
import {workspacePath, workspacePathFromAddress} from './workspacePath';

interface Props {
  pipelinePath: string;
}

export const WorkspacePipelineRoot: React.FC<Props> = (props) => {
  const {pipelinePath} = props;
  const entireMatch = useRouteMatch(['/workspace/pipelines/(/?.*)', '/workspace/jobs/(/?.*)']);
  const location = useLocation();

  const toAppend = entireMatch!.params[0];
  const {search} = location;

  const {pipelineName} = explorerPathFromString(pipelinePath);
  const {loading, options} = useRepositoryOptions();
  const {flagPipelineModeTuples} = useFeatureFlags();

  if (loading) {
    return <LoadingSpinner purpose="page" />;
  }

  const reposWithMatch = findRepoContainingPipeline(options, pipelineName);
  if (reposWithMatch.length === 0) {
    return (
      <NonIdealState
        icon="cube"
        title={flagPipelineModeTuples ? 'No matching jobs' : 'No matching pipelines'}
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
      <Box padding={{horizontal: 24}}>
        <PageHeader
          title={<Heading>{pipelineName}</Heading>}
          icon={flagPipelineModeTuples ? 'workspaces' : 'schema'}
          description={
            flagPipelineModeTuples
              ? 'Job in multiple repositories'
              : 'Pipeline in multiple repositories'
          }
        />
        <Box margin={{vertical: 16}}>
          <Alert
            intent="info"
            title={
              <div>
                {flagPipelineModeTuples ? (
                  <>
                    Jobs named <strong>{pipelineName}</strong> were found in multiple repositories.
                  </>
                ) : (
                  <>
                    Pipelines named <strong>{pipelineName}</strong> were found in multiple
                    repositories.
                  </>
                )}
              </div>
            }
          />
        </Box>
      </Box>
      <Table>
        <thead>
          <tr>
            <th>Repository name and location</th>
            <th>{flagPipelineModeTuples ? 'Job' : 'Pipeline'}</th>
          </tr>
        </thead>
        <tbody>
          {reposWithMatch.map((repository) => {
            const {
              repository: {name},
              repositoryLocation: {name: location},
            } = repository;
            const repoString = buildRepoPath(name, location);
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
