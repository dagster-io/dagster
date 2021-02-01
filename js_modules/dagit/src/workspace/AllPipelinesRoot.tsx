import {gql, useQuery} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Loading} from 'src/ui/Loading';
import {Page} from 'src/ui/Page';
import {Table} from 'src/ui/Table';
import {Heading} from 'src/ui/Text';
import {buildRepoAddress} from 'src/workspace/buildRepoAddress';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {AllPipelinesQuery} from 'src/workspace/types/AllPipelinesQuery';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

const AllPipelinesTable: React.FC<{data: AllPipelinesQuery}> = ({data}) => {
  useDocumentTitle('Pipelines');

  const repositoryLocations =
    data?.repositoryLocationsOrError.__typename === 'RepositoryLocationConnection'
      ? data.repositoryLocationsOrError.nodes
      : null;

  const pipelines = React.useMemo(() => {
    if (!repositoryLocations) {
      return null;
    }
    return repositoryLocations.reduce((accum, location) => {
      if (location.__typename !== 'RepositoryLocation') {
        return accum;
      }
      return [
        ...accum,
        ...location.repositories.reduce((innerAccum, repository) => {
          if (repository.__typename !== 'Repository') {
            return innerAccum;
          }
          const repoAddress = buildRepoAddress(repository.name, location.name);
          return [
            ...innerAccum,
            ...repository.pipelines.map((pipeline) => ({
              repoAddress,
              pipeline,
            })),
          ];
        }, []),
      ];
    }, []);
  }, [repositoryLocations]);

  const sorted = React.useMemo(() => {
    if (pipelines) {
      return [
        ...pipelines.sort((a, b) =>
          a.pipeline.name.toLocaleLowerCase().localeCompare(b.pipeline.name.toLocaleLowerCase()),
        ),
      ];
    }
    return null;
  }, [pipelines]);

  if (!sorted?.length) {
    return (
      <Box flex={{alignItems: 'center', justifyContent: 'center'}} margin={{top: 64}} padding={64}>
        <NonIdealState
          icon="diagram-tree"
          title="No pipelines"
          description="We could not find any pipelines in your current workspace."
        />
      </Box>
    );
  }

  return (
    <Table>
      <thead>
        <tr>
          <th>Pipeline</th>
          <th>Repository</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map(({pipeline, repoAddress}) => (
          <tr key={`${pipeline.name}-${repoAddressAsString(repoAddress)}`}>
            <td>
              <Link to={workspacePathFromAddress(repoAddress, `/pipelines/${pipeline.name}`)}>
                {pipeline.name}
              </Link>
            </td>
            <td>{repoAddressAsString(repoAddress)}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};

export const AllPipelinesRoot = () => {
  const queryResult = useQuery<AllPipelinesQuery>(ALL_PIPELINES_QUERY);
  return (
    <Page style={{height: '100vh', overflowY: 'auto'}}>
      <Group direction="column" spacing={16}>
        <Heading>Pipelines</Heading>
        <Loading queryResult={queryResult}>{(data) => <AllPipelinesTable data={data} />}</Loading>
      </Group>
    </Page>
  );
};

const ALL_PIPELINES_QUERY = gql`
  query AllPipelinesQuery {
    repositoryLocationsOrError {
      __typename
      ... on RepositoryLocationConnection {
        nodes {
          __typename
          ... on RepositoryLocation {
            id
            name
            repositories {
              id
              name
              pipelines {
                id
                name
              }
            }
          }
        }
      }
    }
  }
`;
