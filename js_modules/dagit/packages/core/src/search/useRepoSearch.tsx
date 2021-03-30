import {gql, useQuery} from '@apollo/client';
import Fuse from 'fuse.js';
import * as React from 'react';

import {workspacePath} from '../workspace/workspacePath';

import {SearchResult, SearchResultType} from './types';
import {SearchBootstrapQuery} from './types/SearchBootstrapQuery';
import {SearchSecondaryQuery} from './types/SearchSecondaryQuery';

const fuseOptions = {
  keys: ['label', 'tags', 'type'],
  limit: 10,
  threshold: 0.3,
};

const bootstrapDataToSearchResults = (data?: SearchBootstrapQuery) => {
  if (
    !data?.repositoryLocationsOrError ||
    data?.repositoryLocationsOrError?.__typename !== 'RepositoryLocationConnection'
  ) {
    return new Fuse([]);
  }

  const {nodes} = data.repositoryLocationsOrError;
  const manyRepos = nodes.length > 1;

  const allEntries = nodes.reduce((accum, repoLocation) => {
    if (repoLocation.__typename === 'RepositoryLocationLoadFailure') {
      return accum;
    }

    const repos = repoLocation.repositories;
    return [
      ...accum,
      ...repos.reduce((inner, repo) => {
        const {name, partitionSets, pipelines, schedules, sensors} = repo;
        const {name: locationName} = repoLocation;
        const repoAddress = `${name}@${locationName}`;

        const allPipelines = pipelines.map((pipeline) => ({
          key: `${repoAddress}-${pipeline.name}`,
          label: pipeline.name,
          description: manyRepos ? `Pipeline in ${repoAddress}` : 'Pipeline',
          href: workspacePath(name, locationName, `/pipelines/${pipeline.name}`),
          type: SearchResultType.Pipeline,
        }));

        const allSchedules = schedules.map((schedule) => ({
          key: `${repoAddress}-${schedule.name}`,
          label: schedule.name,
          description: manyRepos ? `Schedule in ${repoAddress}` : 'Schedule',
          href: workspacePath(name, locationName, `/schedules/${schedule.name}`),
          type: SearchResultType.Schedule,
        }));

        const allSensors = sensors.map((sensor) => ({
          key: `${repoAddress}-${sensor.name}`,
          label: sensor.name,
          description: manyRepos ? `Sensor in ${repoAddress}` : 'Sensor',
          href: workspacePath(name, locationName, `/sensors/${sensor.name}`),
          type: SearchResultType.Sensor,
        }));

        const allPartitionSets = partitionSets.map((partitionSet) => ({
          key: `${repoAddress}-${partitionSet.name}`,
          label: partitionSet.name,
          description: manyRepos ? `Partition set in ${repoAddress}` : 'Partition set',
          href: workspacePath(
            name,
            locationName,
            `/pipelines/${partitionSet.pipelineName}/partitions?partitionSet=${partitionSet.name}`,
          ),
          type: SearchResultType.PartitionSet,
        }));

        return [...inner, ...allPipelines, ...allSchedules, ...allSensors, ...allPartitionSets];
      }, []),
    ];
  }, []);

  return new Fuse(allEntries, fuseOptions);
};

const secondaryDataToSearchResults = (data?: SearchSecondaryQuery) => {
  if (!data?.assetsOrError || data.assetsOrError.__typename === 'PythonError') {
    return new Fuse([]);
  }

  const {nodes} = data.assetsOrError;
  const allEntries = nodes.map((node) => {
    const {key, tags} = node;
    const path = key.path.join(' › ');
    return {
      key: path,
      label: path,
      description: 'Asset',
      href: `/instance/assets/${key.path.join('/')}`,
      type: SearchResultType.Asset,
      tags: tags.map((tag) => `${tag.key}:${tag.value}`).join(' '),
    };
  });

  return new Fuse(allEntries, fuseOptions);
};

export const useRepoSearch = () => {
  const {data: bootstrapData, loading: bootstrapLoading} = useQuery<SearchBootstrapQuery>(
    SEARCH_BOOTSTRAP_QUERY,
    {
      fetchPolicy: 'cache-and-network',
    },
  );

  const {data: secondaryData, loading: secondaryLoading} = useQuery<SearchSecondaryQuery>(
    SEARCH_SECONDARY_QUERY,
    {
      fetchPolicy: 'cache-and-network',
    },
  );

  const bootstrapFuse = React.useMemo(() => bootstrapDataToSearchResults(bootstrapData), [
    bootstrapData,
  ]);
  const secondaryFuse = React.useMemo(() => secondaryDataToSearchResults(secondaryData), [
    secondaryData,
  ]);

  const loading = bootstrapLoading || secondaryLoading;
  const performSearch = React.useCallback(
    (queryString: string): Fuse.FuseResult<SearchResult>[] => {
      const bootstrapResults = bootstrapFuse.search(queryString);
      const secondaryResults = secondaryFuse.search(queryString);
      return [...bootstrapResults, ...secondaryResults];
    },
    [bootstrapFuse, secondaryFuse],
  );

  return {loading, performSearch};
};

const SEARCH_BOOTSTRAP_QUERY = gql`
  query SearchBootstrapQuery {
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
              ... on Repository {
                id
                name
                pipelines {
                  id
                  name
                }
                schedules {
                  id
                  name
                }
                sensors {
                  id
                  name
                }
                partitionSets {
                  id
                  name
                  pipelineName
                }
              }
            }
          }
        }
      }
    }
  }
`;

const SEARCH_SECONDARY_QUERY = gql`
  query SearchSecondaryQuery {
    assetsOrError {
      __typename
      ... on AssetConnection {
        nodes {
          key {
            path
          }
          tags {
            key
            value
          }
        }
      }
    }
  }
`;
