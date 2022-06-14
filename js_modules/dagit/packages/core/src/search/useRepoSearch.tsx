import {gql, useLazyQuery} from '@apollo/client';
import Fuse from 'fuse.js';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {displayNameForAssetKey, isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {buildRepoPath} from '../workspace/buildRepoAddress';
import {workspacePath} from '../workspace/workspacePath';

import {SearchResult, SearchResultType} from './types';
import {
  SearchBootstrapQuery,
  SearchBootstrapQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories as Repository,
} from './types/SearchBootstrapQuery';
import {SearchSecondaryQuery} from './types/SearchSecondaryQuery';

const fuseOptions = {
  keys: ['label', 'segments', 'tags', 'type'],
  limit: 10,
  threshold: 0.5,
  useExtendedSearch: true,
};

const bootstrapDataToSearchResults = (data?: SearchBootstrapQuery) => {
  if (!data?.workspaceOrError || data?.workspaceOrError?.__typename !== 'Workspace') {
    return new Fuse([]);
  }

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
        const {name: repoName, partitionSets, pipelines, schedules, sensors} = repo;
        const {name: locationName} = repoLocation;
        const repoPath = buildRepoPath(repoName, locationName);

        const allPipelinesAndJobs = pipelines
          .filter((item) => !isHiddenAssetGroupJob(item.name))
          .reduce((flat, pipelineOrJob) => {
            const {name, isJob} = pipelineOrJob;
            return [
              ...flat,
              {
                label: name,
                description: manyRepos
                  ? `${isJob ? 'Job' : 'Pipeline'} in ${repoPath}`
                  : isJob
                  ? 'Job'
                  : 'Pipeline',
                href: workspacePath(
                  repoName,
                  locationName,
                  `/${isJob ? 'jobs' : 'pipelines'}/${name}`,
                ),
                type: SearchResultType.Pipeline,
              },
            ];
          }, [] as SearchResult[]);

        const allSchedules: SearchResult[] = schedules.map((schedule) => ({
          label: schedule.name,
          description: manyRepos ? `Schedule in ${repoPath}` : 'Schedule',
          href: workspacePath(repoName, locationName, `/schedules/${schedule.name}`),
          type: SearchResultType.Schedule,
        }));

        const allSensors: SearchResult[] = sensors.map((sensor) => ({
          label: sensor.name,
          description: manyRepos ? `Sensor in ${repoPath}` : 'Sensor',
          href: workspacePath(repoName, locationName, `/sensors/${sensor.name}`),
          type: SearchResultType.Sensor,
        }));

        const allPartitionSets: SearchResult[] = partitionSets
          .filter((item) => !isHiddenAssetGroupJob(item.pipelineName))
          .map((partitionSet) => ({
            label: partitionSet.name,
            description: manyRepos ? `Partition set in ${repoPath}` : 'Partition set',
            href: workspacePath(
              repoName,
              locationName,
              `/pipeline_or_job/${partitionSet.pipelineName}/partitions?partitionSet=${partitionSet.name}`,
            ),
            type: SearchResultType.PartitionSet,
          }));

        return [
          ...inner,
          ...allPipelinesAndJobs,
          ...allSchedules,
          ...allSensors,
          ...allPartitionSets,
        ];
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
  const allEntries = nodes.map(({key}) => {
    return {
      label: displayNameForAssetKey(key),
      href: assetDetailsPathForKey(key),
      segments: key.path,
      description: 'Asset',
      type: SearchResultType.Asset,
    };
  });

  return new Fuse(allEntries, fuseOptions);
};

export const useRepoSearch = () => {
  const [
    performBootstrapQuery,
    {data: bootstrapData, loading: bootstrapLoading},
  ] = useLazyQuery<SearchBootstrapQuery>(SEARCH_BOOTSTRAP_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  const [
    performSecondaryQuery,
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
        performSecondaryQuery();
      }
      const bootstrapResults: Fuse.FuseResult<SearchResult>[] = bootstrapFuse.search(queryString);
      const secondaryResults: Fuse.FuseResult<SearchResult>[] = secondaryFuse.search(queryString);
      return [...bootstrapResults, ...secondaryResults];
    },
    [bootstrapFuse, secondaryFuse, performSecondaryQuery, secondaryQueryCalled],
  );

  return {performBootstrapQuery, loading, performSearch};
};

const SEARCH_BOOTSTRAP_QUERY = gql`
  query SearchBootstrapQuery {
    workspaceOrError {
      __typename
      ...PythonErrorFragment
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
                    isJob
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
    materializedKeysOrError {
      __typename
      ... on MaterializedKeysConnection {
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
