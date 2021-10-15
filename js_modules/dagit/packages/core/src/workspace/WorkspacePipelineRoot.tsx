import * as React from 'react';
import {Link, Redirect, useLocation, useRouteMatch} from 'react-router-dom';

import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {LoadingSpinner} from '../ui/Loading';
import {NonIdealState} from '../ui/NonIdealState';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Table} from '../ui/Table';
import {Heading} from '../ui/Text';

import {isThisThingAJob, optionToRepoAddress, useRepositoryOptions} from './WorkspaceContext';
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

  if (loading) {
    return <LoadingSpinner purpose="page" />;
  }

  const reposWithMatch = findRepoContainingPipeline(options, pipelineName);
  if (reposWithMatch.length === 0) {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState
          icon="no-results"
          title="No matching jobs"
          description={
            <div>
              <div>
                <strong>{pipelineName}</strong>
              </div>
              was not found in any repositories in this workspace.
            </div>
          }
        />
      </Box>
    );
  }

  if (reposWithMatch.length === 1) {
    const match = reposWithMatch[0];
    const repoAddress = optionToRepoAddress(match);
    const isJob = isThisThingAJob(match, pipelineName);
    const to = workspacePathFromAddress(
      repoAddress,
      `/${isJob ? 'jobs' : 'pipelines'}/${toAppend}${search}`,
    );
    return <Redirect to={to} />;
  }

  const anyPipelines = reposWithMatch.some((repo) => !isThisThingAJob(repo, pipelineName));

  return (
    <Page>
      <PageHeader
        title={<Heading>{pipelineName}</Heading>}
        icon="job"
        description={
          anyPipelines ? 'Job / pipeline in multiple repositories' : 'Job in multiple repositories'
        }
      />
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Alert
          intent="info"
          title={
            <div>
              {anyPipelines ? (
                <>
                  Jobs or pipelines named <strong>{pipelineName}</strong> were found in multiple
                  repositories.
                </>
              ) : (
                <>
                  Jobs named <strong>{pipelineName}</strong> were found in multiple repositories.
                </>
              )}
            </div>
          }
        />
      </Box>
      <Table>
        <thead>
          <tr>
            <th>Repository name and location</th>
            <th>{anyPipelines ? 'Job / Pipeline' : 'Job'}</th>
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
                  <Link
                    to={workspacePath(
                      name,
                      location,
                      `/${
                        isThisThingAJob(repository, pipelineName) ? 'jobs' : 'pipelines'
                      }/${pipelineName}`,
                    )}
                  >
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
