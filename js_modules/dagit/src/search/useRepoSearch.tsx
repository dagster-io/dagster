import {gql, useQuery} from '@apollo/client';
import Fuse from 'fuse.js';
import * as React from 'react';

import {SearchResult, SearchResultType} from 'src/search/types';
import {SearchBootstrapQuery} from 'src/search/types/SearchBootstrapQuery';
import {workspacePath} from 'src/workspace/workspacePath';

const fuseOptions = {
  keys: ['label', 'tags', 'type'],
  limit: 10,
  threshold: 0.3,
};

const repositoryDataToSearchResults = (data?: SearchBootstrapQuery) => {
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
        const {name, pipelines, schedules, sensors} = repo;
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

        return [...inner, ...allPipelines, ...allSchedules, ...allSensors];
      }, []),
    ];
  }, []);

  return new Fuse(allEntries, fuseOptions);
};

export const useRepoSearch = () => {
  const {data} = useQuery<SearchBootstrapQuery>(SEARCH_BOOTSTRAP_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  const fuse = React.useMemo(() => repositoryDataToSearchResults(data), [data]);
  return React.useCallback(
    (queryString: string): Fuse.FuseResult<SearchResult>[] => fuse.search(queryString),
    [fuse],
  );
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
                }
              }
            }
          }
        }
      }
    }
  }
`;
