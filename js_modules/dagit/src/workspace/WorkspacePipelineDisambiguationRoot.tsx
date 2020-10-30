import {useQuery} from '@apollo/client';
import {Callout, IBreadcrumbProps, NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Loading} from 'src/Loading';
import {TopNav} from 'src/nav/TopNav';
import {Page} from 'src/ui/Page';
import {Table} from 'src/ui/Table';
import {ROOT_REPOSITORIES_QUERY} from 'src/workspace/WorkspaceContext';
import {RootRepositoriesQuery} from 'src/workspace/types/RootRepositoriesQuery';
import {workspacePath} from 'src/workspace/workspacePath';

type Props = {
  pipelineName: string;
};

export const WorkspacePipelineDisambiguationRoot: React.FunctionComponent<Props> = (
  props: Props,
) => {
  const {pipelineName} = props;

  const queryResult = useQuery<RootRepositoriesQuery>(ROOT_REPOSITORIES_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  const breadcrumbs: IBreadcrumbProps[] = [
    {icon: 'cube', text: 'Workspace', href: '/workspace'},
    {text: `Pipeline: ${pipelineName}`},
  ];

  return (
    <>
      <TopNav breadcrumbs={breadcrumbs} />
      <Loading queryResult={queryResult}>
        {(data) => {
          const {repositoriesOrError} = data;
          if (repositoriesOrError.__typename === 'PythonError') {
            return (
              <NonIdealState
                icon="cube"
                title="Error loading repositories"
                description="Could not load repositories in this workspace."
              />
            );
          }

          const {nodes} = repositoriesOrError;
          const matches = nodes.filter((repo) =>
            repo.pipelines.some((pipeline) => pipeline.name === pipelineName),
          );

          if (!matches.length) {
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

          return (
            <Page>
              <Callout intent="primary" icon="info-sign" style={{marginBottom: '12px'}}>
                Pipelines named <strong>{pipelineName}</strong> were found in multiple repositories.
              </Callout>
              <Table striped style={{width: '100%'}}>
                <thead>
                  <tr>
                    <th>Repository name and location</th>
                    <th>Pipeline</th>
                  </tr>
                </thead>
                <tbody>
                  {matches.map((repository) => {
                    const {
                      name,
                      location: {name: location},
                    } = repository;
                    const repoAddress = `${name}@${location}`;
                    return (
                      <tr key={repoAddress}>
                        <td style={{width: '40%'}}>{repoAddress}</td>
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
        }}
      </Loading>
    </>
  );
};
