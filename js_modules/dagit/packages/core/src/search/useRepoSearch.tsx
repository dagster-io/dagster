import {gql, useLazyQuery, useQuery} from '@apollo/client';
import Fuse from 'fuse.js';
import * as React from 'react';

import {featureEnabled, FeatureFlag} from '../app/Flags';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {buildRepoPath} from '../workspace/buildRepoAddress';
import {workspacePath} from '../workspace/workspacePath';

import {SearchResult, SearchResultType} from './types';
import {
  SearchBootstrapQuery,
  SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories as Repository,
} from './types/SearchBootstrapQuery';
import {SearchSecondaryQuery} from './types/SearchSecondaryQuery';

const fuseOptions = {
  keys: ['label', 'tags', 'type'],
  limit: 10,
  threshold: 0.3,
  useExtendedSearch: true,
};

const bootstrapDataToSearchResults = (data?: SearchBootstrapQuery) => {
  if (!data?.workspaceOrError || data?.workspaceOrError?.__typename !== 'Workspace') {
    return new Fuse([]);
  }

  const pipelineMode = featureEnabled(FeatureFlag.flagPipelineModeTuples);
  const {locationEntries} = data.workspaceOrError;
  const manyRepos = locationEntries.length > 1;

  const allEntries = locationEntries.reduce((accum, locationEntry) => {
    if (locationEntry.locationOrLoadError?.__typename !== 'RepositoryLocation') {
      return accum;
    }

    const repoLocation = locationEntry.locationOrLoadError;
    const repos: Repository[] = repoLocation.repositories;
    return [
      ...accum,
      ...repos.reduce((inner, repo) => {
        const {name, partitionSets, pipelines, schedules, sensors} = repo;
        const {name: locationName} = repoLocation;
        const repoPath = buildRepoPath(name, locationName);

        const allPipelines = pipelineMode
          ? pipelines.reduce((flat, pipeline) => {
              const jobs = pipeline.modes.map((mode) => ({
                key: `${repoPath}-${pipeline.name}-${mode.name}`,
                label: `${pipeline.name} : ${mode.name}`,
                description: manyRepos ? `Job in ${repoPath}` : 'Job',
                href: workspacePath(name, locationName, `/pipelines/${pipeline.name}:${mode.name}`),
                type: SearchResultType.Pipeline,
              }));
              return [...flat, ...jobs];
            }, [] as SearchResult[])
          : pipelines.map((pipeline) => ({
              key: `${repoPath}-${pipeline.name}`,
              label: pipeline.name,
              description: manyRepos ? `Pipeline in ${repoPath}` : 'Pipeline',
              href: workspacePath(name, locationName, `/pipelines/${pipeline.name}`),
              type: SearchResultType.Pipeline,
            }));

        const allSchedules = schedules.map((schedule) => ({
          key: `${repoPath}-${schedule.name}`,
          label: schedule.name,
          description: manyRepos ? `Schedule in ${repoPath}` : 'Schedule',
          href: workspacePath(name, locationName, `/schedules/${schedule.name}`),
          type: SearchResultType.Schedule,
        }));

        const allSensors = sensors.map((sensor) => ({
          key: `${repoPath}-${sensor.name}`,
          label: sensor.name,
          description: manyRepos ? `Sensor in ${repoPath}` : 'Sensor',
          href: workspacePath(name, locationName, `/sensors/${sensor.name}`),
          type: SearchResultType.Sensor,
        }));

        const allPartitionSets = partitionSets.map((partitionSet) => ({
          key: `${repoPath}-${partitionSet.name}`,
          label: partitionSet.name,
          description: manyRepos ? `Partition set in ${repoPath}` : 'Partition set',
          href: workspacePath(
            name,
            locationName,
            `/pipelines/${partitionSet.pipelineName}/partitions?partitionSet=${partitionSet.name}`,
          ),
          type: SearchResultType.PartitionSet,
        }));

        return [...inner, ...allPipelines, ...allSchedules, ...allSensors, ...allPartitionSets];
      }, [] as SearchResult[]),
    ];
  }, [] as SearchResult[]);

  return new Fuse(allEntries, fuseOptions);
};

const secondaryDataToSearchResults = (data?: SearchSecondaryQuery) => {
  if (!data?.assetsOrError || data.assetsOrError.__typename === 'PythonError') {
    return new Fuse([]);
  }

  const {nodes} = data.assetsOrError;
  const allEntries = nodes.map((node) => {
    const {key} = node;
    const path = key.path.join(' › ');
    return {
      key: path,
      label: path,
      description: 'Asset',
      href: `/instance/assets/${key.path.map(encodeURIComponent).join('/')}`,
      type: SearchResultType.Asset,
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

  const [
    performQuery,
    {data: secondaryData, loading: secondaryLoading, called: secondaryQueryCalled},
  ] = useLazyQuery<SearchSecondaryQuery>(SEARCH_SECONDARY_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  const bootstrapFuse = React.useMemo(() => bootstrapDataToSearchResults(bootstrapData), [
    bootstrapData,
  ]);
  const secondaryFuse = React.useMemo(() => secondaryDataToSearchResults(secondaryData), [
    secondaryData,
  ]);
  const loading = bootstrapLoading || secondaryLoading;
  const performSearch = React.useCallback(
    (queryString: string, buildSecondary?: boolean): Fuse.FuseResult<SearchResult>[] => {
      if ((queryString || buildSecondary) && !secondaryQueryCalled) {
        performQuery();
      }
      const bootstrapResults: Fuse.FuseResult<SearchResult>[] = bootstrapFuse.search(queryString);
      const secondaryResults: Fuse.FuseResult<SearchResult>[] = secondaryFuse.search(queryString);
      return [...bootstrapResults, ...secondaryResults];
    },
    [bootstrapFuse, secondaryFuse, performQuery, secondaryQueryCalled],
  );

  return {loading, performSearch};
};

const SEARCH_BOOTSTRAP_QUERY = gql`
  query SearchBootstrapQuery {
    workspaceOrError {
      __typename
      ... on PythonError {
        ...PythonErrorFragment
      }
      ... on Workspace {
        locationEntries {
          __typename
          id
          locationOrLoadError {
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
                    modes {
                      id
                      name
                    }
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
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

const SEARCH_SECONDARY_QUERY = gql`
  query SearchSecondaryQuery {
    assetsOrError {
      __typename
      ... on AssetConnection {
        nodes {
          id
          key {
            path
          }
        }
      }
    }
  }
`;
