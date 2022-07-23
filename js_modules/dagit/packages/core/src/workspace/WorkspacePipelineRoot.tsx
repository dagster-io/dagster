import {Alert, Box, NonIdealState, Page, PageHeader, Table, Heading} from '@dagster-io/ui';
import * as React from 'react';
import {Link, Redirect, useLocation, useParams, useRouteMatch} from 'react-router-dom';

import {useTrackPageView} from '../app/analytics';
import {explorerPathFromString} from '../pipelines/PipelinePathUtils';
import {LoadingSpinner} from '../ui/Loading';

import {isThisThingAJob, optionToRepoAddress, useRepositoryOptions} from './WorkspaceContext';
import {buildRepoPath} from './buildRepoAddress';
import {findRepoContainingPipeline} from './findRepoContainingPipeline';
import {workspacePath, workspacePathFromAddress} from './workspacePath';

export const WorkspacePipelineRoot = () => {
  useTrackPageView();

  const params = useParams<{pipelinePath: string}>();
  const {pipelinePath} = params;

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
