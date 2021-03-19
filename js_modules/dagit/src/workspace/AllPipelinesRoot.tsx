import {gql, useQuery} from '@apollo/client';
import {Colors, NonIdealState} from '@blueprintjs/core';
import Fuse from 'fuse.js';
import * as React from 'react';
import styled from 'styled-components/macro';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {PipelineForTable, PipelineTable, PIPELINE_TABLE_FRAGMENT} from '../pipelines/PipelineTable';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';
import {Code, Heading} from '../ui/Text';

import {buildRepoAddress} from './buildRepoAddress';
import {repoAddressAsString} from './repoAddressAsString';
import {AllPipelinesQuery} from './types/AllPipelinesQuery';

const fuseOptions = {
  keys: ['name', 'repo', 'description'],
  threshold: 0.3,
};

const buildKey = (pipelineName: string, repo: string) => `${pipelineName}-${repo}`;

const AllPipelinesTable: React.FC<{data: AllPipelinesQuery}> = ({data}) => {
  useDocumentTitle('Pipelines');

  const [queryString, setQueryString] = React.useState('');

  const repositoryLocations =
    data?.repositoryLocationsOrError.__typename === 'RepositoryLocationConnection'
      ? data.repositoryLocationsOrError.nodes
      : null;

  const pipelineMap: {
    [key: string]: PipelineForTable;
  } = React.useMemo(() => {
    if (!repositoryLocations) {
      return {};
    }

    const allPipelines: {[key: string]: PipelineForTable} = {};
    repositoryLocations.forEach((location) => {
      if (location.__typename === 'RepositoryLocation') {
        const {repositories} = location;
        repositories.forEach((repo) => {
          const repoAddress = buildRepoAddress(repo.name, location.name);
          repo.pipelines.forEach((pipeline) => {
            const key = buildKey(pipeline.name, repoAddressAsString(repoAddress));
            allPipelines[key] = {pipeline, repoAddress};
          });
        });
      }
    });

    return allPipelines;
  }, [repositoryLocations]);

  const repoCount = React.useMemo(() => {
    return (repositoryLocations || []).reduce(
      (accum, location) =>
        accum + (location.__typename === 'RepositoryLocation' ? location.repositories.length : 0),
      0,
    );
  }, [repositoryLocations]);

  const fuse = React.useMemo(() => {
    const allEntries = Object.keys(pipelineMap).map((pipelineKey) => {
      const {pipeline, repoAddress} = pipelineMap[pipelineKey];
      return {
        name: pipeline.name,
        description: pipeline.description,
        repo: repoAddressAsString(repoAddress),
      };
    });
    return new Fuse(allEntries, fuseOptions);
  }, [pipelineMap]);

  const matches = fuse.search(queryString);

  const matchingResults = React.useMemo(() => {
    if (!queryString) {
      return Object.keys(pipelineMap)
        .map((key) => pipelineMap[key])
        .sort((a, b) =>
          a.pipeline.name.toLocaleLowerCase().localeCompare(b.pipeline.name.toLocaleLowerCase()),
        );
    }
    return [...matches.map((match) => pipelineMap[buildKey(match.item.name, match.item.repo)])];
  }, [matches, pipelineMap, queryString]);

  const onChange = React.useCallback((e) => setQueryString(e.target.value), []);

  const content = () => {
    if (!matchingResults?.length) {
      const searchMiss = queryString && Object.keys(pipelineMap).length;
      const description = searchMiss ? (
        <div>
          We could not find any pipelines matching{' '}
          <Code style={{fontSize: 'inherit'}}>{queryString}</Code>.
        </div>
      ) : (
        'We could not find any pipelines in your current workspace.'
      );

      return (
        <Box
          flex={{alignItems: 'center', justifyContent: 'center'}}
          margin={{top: 64}}
          padding={64}
        >
          <NonIdealState
            icon="diagram-tree"
            title={searchMiss ? 'No matches' : 'No pipelines'}
            description={description}
          />
        </Box>
      );
    }

    return <PipelineTable pipelines={matchingResults} showRepo={repoCount > 1} />;
  };

  return (
    <Group direction="column" spacing={12}>
      <PipelineFilterInput
        type="text"
        placeholder="Search pipelines…"
        value={queryString}
        onChange={onChange}
        spellCheck={false}
        autoCorrect="off"
      />
      {content()}
    </Group>
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

const PipelineFilterInput = styled.input`
  border: 1px solid ${Colors.LIGHT_GRAY1};
  border-radius: 3px;
  color: ${Colors.DARK_GRAY3};
  font-size: 14px;
  padding: 8px;
  width: 45%;
  min-width: 380px;
  max-width: 700px;

  :focus {
    outline: none;
  }

  ::placeholder {
    color: ${Colors.GRAY3};
  }
`;

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
                ...PipelineTableFragment
              }
            }
          }
        }
      }
    }
  }
  ${PIPELINE_TABLE_FRAGMENT}
`;
