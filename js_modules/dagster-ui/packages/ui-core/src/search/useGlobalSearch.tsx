import {gql} from '@apollo/client';
import qs from 'qs';
import {useCallback, useEffect, useRef} from 'react';

import {QueryResponse, WorkerSearchResult, createSearchWorker} from './createSearchWorker';
import {AssetFilterSearchResultType, SearchResult, SearchResultType} from './types';
import {
  SearchPrimaryQuery,
  SearchPrimaryQueryVariables,
  SearchSecondaryQuery,
  SearchSecondaryQueryVariables,
} from './types/useGlobalSearch.types';
import {useIndexedDBCachedQuery} from './useIndexedDBCachedQuery';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {displayNameForAssetKey, isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {
  GroupMetadata,
  buildAssetCountBySection,
  linkToCodeLocation,
} from '../assets/AssetsOverview';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';
import {workspacePath} from '../workspace/workspacePath';

const linkToAssetTableWithGroupFilter = (groupMetadata: GroupMetadata) => {
  return `/assets?${qs.stringify({groups: JSON.stringify([groupMetadata])})}`;
};

const linkToAssetTableWithComputeKindFilter = (computeKind: string) => {
  return `/assets?${qs.stringify({
    computeKindTags: JSON.stringify([computeKind]),
  })}`;
};

const linkToAssetTableWithOwnerFilter = (owner: string) => {
  return `/assets?${qs.stringify({
    owners: JSON.stringify([owner]),
  })}`;
};

const primaryDataToSearchResults = (input: {data?: SearchPrimaryQuery}) => {
  const {data} = input;

  if (!data?.workspaceOrError || data?.workspaceOrError?.__typename !== 'Workspace') {
    return [];
  }

  const {locationEntries} = data.workspaceOrError;
  const firstEntry = locationEntries[0];
  const manyLocations =
    locationEntries.length > 1 ||
    (firstEntry &&
      firstEntry.__typename === 'WorkspaceLocationEntry' &&
      firstEntry.locationOrLoadError?.__typename === 'RepositoryLocation' &&
      firstEntry.locationOrLoadError.repositories.length > 1);

  const allEntries = locationEntries.reduce((accum, locationEntry) => {
    if (locationEntry.locationOrLoadError?.__typename !== 'RepositoryLocation') {
      return accum;
    }

    const repoLocation = locationEntry.locationOrLoadError;
    const repos = repoLocation.repositories;
    return [
      ...accum,
      ...repos.reduce((inner, repo) => {
        const {
          name: repoName,
          assetGroups,
          partitionSets,
          pipelines,
          schedules,
          sensors,
          allTopLevelResourceDetails,
        } = repo;
        const {name: locationName} = repoLocation;
        const repoPath = buildRepoPathForHuman(repoName, locationName);

        const allAssetGroups = assetGroups.reduce((flat, assetGroup) => {
          const {groupName} = assetGroup;
          return [
            ...flat,
            {
              label: groupName,
              description: manyLocations ? `Asset group in ${repoPath}` : 'Asset group',
              href: workspacePath(repoName, locationName, `/asset-groups/${groupName}`),
              type: SearchResultType.AssetGroup,
            },
          ];
        }, [] as SearchResult[]);

        const allPipelinesAndJobs = pipelines
          .filter((item) => !isHiddenAssetGroupJob(item.name))
          .reduce((flat, pipelineOrJob) => {
            const {name, isJob} = pipelineOrJob;
            return [
              ...flat,
              {
                label: name,
                description: manyLocations
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
          description: manyLocations ? `Schedule in ${repoPath}` : 'Schedule',
          href: workspacePath(repoName, locationName, `/schedules/${schedule.name}`),
          type: SearchResultType.Schedule,
        }));

        const allSensors: SearchResult[] = sensors.map((sensor) => ({
          label: sensor.name,
          description: manyLocations ? `Sensor in ${repoPath}` : 'Sensor',
          href: workspacePath(repoName, locationName, `/sensors/${sensor.name}`),
          type: SearchResultType.Sensor,
        }));

        const allResources: SearchResult[] = allTopLevelResourceDetails.map((resource) => ({
          label: resource.name,
          description: manyLocations ? `Resource in ${repoPath}` : 'Resource',
          href: workspacePath(repoName, locationName, `/resources/${resource.name}`),
          type: SearchResultType.Resource,
        }));

        const allPartitionSets: SearchResult[] = partitionSets
          .filter((item) => !isHiddenAssetGroupJob(item.pipelineName))
          .map((partitionSet) => ({
            label: partitionSet.name,
            description: manyLocations ? `Partition set in ${repoPath}` : 'Partition set',
            href: workspacePath(
              repoName,
              locationName,
              `/pipeline_or_job/${partitionSet.pipelineName}/partitions?partitionSet=${partitionSet.name}`,
            ),
            type: SearchResultType.PartitionSet,
          }));

        return [
          ...inner,
          ...allAssetGroups,
          ...allPipelinesAndJobs,
          ...allSchedules,
          ...allSensors,
          ...allPartitionSets,
          ...allResources,
        ];
      }, [] as SearchResult[]),
    ];
  }, [] as SearchResult[]);

  return allEntries;
};

const secondaryDataToSearchResults = (
  input: {data?: SearchSecondaryQuery},
  includeAssetFilters: boolean,
) => {
  const {data} = input;
  if (!data?.assetsOrError || data.assetsOrError.__typename === 'PythonError') {
    return [];
  }

  const {nodes} = data.assetsOrError;

  const assets = nodes
    .filter(({definition}) => definition !== null)
    .map(({key, definition}) => {
      return {
        label: displayNameForAssetKey(key),
        href: assetDetailsPathForKey(key),
        segments: key.path,
        description: `Asset in ${buildRepoPathForHuman(
          definition!.repository.name,
          definition!.repository.location.name,
        )}`,
        type: SearchResultType.Asset,
      };
    });

  if (!includeAssetFilters) {
    return [...assets];
  } else {
    const countsBySection = buildAssetCountBySection(nodes);

    const computeKindResults: SearchResult[] = Object.entries(
      countsBySection.countsByComputeKind,
    ).map(([computeKind, count]) => ({
      label: computeKind,
      description: '',
      type: AssetFilterSearchResultType.ComputeKind,
      href: linkToAssetTableWithComputeKindFilter(computeKind),
      numResults: count,
    }));

    const codeLocationResults: SearchResult[] = countsBySection.countPerCodeLocation.map(
      (codeLocationAssetCount) => ({
        label: buildRepoPathForHuman(
          codeLocationAssetCount.repoAddress.name,
          codeLocationAssetCount.repoAddress.location,
        ),
        description: '',
        type: AssetFilterSearchResultType.CodeLocation,
        href: linkToCodeLocation(codeLocationAssetCount.repoAddress),
        numResults: codeLocationAssetCount.assetCount,
      }),
    );

    const groupResults: SearchResult[] = countsBySection.countPerAssetGroup.map(
      (groupAssetCount) => ({
        label: groupAssetCount.groupMetadata.groupName,
        description: '',
        type: AssetFilterSearchResultType.AssetGroup,
        href: linkToAssetTableWithGroupFilter(groupAssetCount.groupMetadata),
        numResults: groupAssetCount.assetCount,
      }),
    );

    const ownerResults: SearchResult[] = Object.entries(countsBySection.countsByOwner).map(
      ([owner, count]) => ({
        label: owner,
        description: '',
        type: AssetFilterSearchResultType.Owner,
        href: linkToAssetTableWithOwnerFilter(owner),
        numResults: count,
      }),
    );
    return [
      ...assets,
      ...computeKindResults,
      ...codeLocationResults,
      ...ownerResults,
      ...groupResults,
    ];
  }
};

const fuseOptions = {
  keys: ['label', 'segments', 'tags', 'type'],
  threshold: 0.3,
  useExtendedSearch: true,
  includeMatches: true,
};

const EMPTY_RESPONSE = {queryString: '', results: []};

type IndexBuffer = {
  query: string;
  resolve: (value: QueryResponse) => void;
  cancel: () => void;
};

// These are the versions of the primary and secondary data queries. They are used to
// version the cache in indexedDB. When the data in the cache must be invalidated, this version
// should be bumped to prevent fetching stale data.
export const SEARCH_PRIMARY_DATA_VERSION = 1;
export const SEARCH_SECONDARY_DATA_VERSION = 1;

/**
 * Perform global search populated by two lazy queries, to be initialized upon some
 * interaction with the search input. Each query result list is packaged and sent to a worker
 * thread, where we use Fuse.js to respond to querystring searches with matching results.
 *
 * This is done in separate queries so that we can provide results quickly for objects
 * that are already most likely fetched in the app, via the "primary" query.
 *
 * Since the queries use our default fetchPolicy of `cache-and-network`, reopening search
 * will show cached results that can be searched, and the queries will be repeated.
 * When they are complete, the workers will be updated with the fresh data.
 *
 * A `terminate` function is provided, but it's probably not necessary to use it.
 */
export const useGlobalSearch = ({includeAssetFilters}: {includeAssetFilters: boolean}) => {
  const primarySearch = useRef<WorkerSearchResult | null>(null);
  const secondarySearch = useRef<WorkerSearchResult | null>(null);

  const {
    data: primaryData,
    fetch: fetchPrimaryData,
    loading: primaryDataLoading,
  } = useIndexedDBCachedQuery<SearchPrimaryQuery, SearchPrimaryQueryVariables>({
    query: SEARCH_PRIMARY_QUERY,
    key: 'SearchPrimary',
    version: SEARCH_PRIMARY_DATA_VERSION,
  });

  const {
    data: secondaryData,
    fetch: fetchSecondaryData,
    loading: secondaryDataLoading,
  } = useIndexedDBCachedQuery<SearchSecondaryQuery, SearchSecondaryQueryVariables>({
    query: SEARCH_SECONDARY_QUERY,
    key: 'SearchSecondary',
    version: SEARCH_SECONDARY_DATA_VERSION,
  });

  const consumeBufferEffect = useCallback(
    async (buffer: React.MutableRefObject<IndexBuffer | null>, search: WorkerSearchResult) => {
      const bufferValue = buffer.current;
      if (bufferValue) {
        buffer.current = null;
        const result = await search.search(bufferValue.query);
        bufferValue.resolve(result);
      }
    },
    [],
  );

  useEffect(() => {
    if (!primaryData) {
      return;
    }
    const results = primaryDataToSearchResults({data: primaryData});
    if (!primarySearch.current) {
      primarySearch.current = createSearchWorker('primary', fuseOptions);
    }
    primarySearch.current.update(results);
    consumeBufferEffect(primarySearchBuffer, primarySearch.current);
  }, [consumeBufferEffect, primaryData]);

  useEffect(() => {
    if (!secondaryData) {
      return;
    }
    const results = secondaryDataToSearchResults({data: secondaryData}, includeAssetFilters);
    if (!secondarySearch.current) {
      secondarySearch.current = createSearchWorker('secondary', fuseOptions);
    }
    secondarySearch.current.update(results);
    consumeBufferEffect(secondarySearchBuffer, secondarySearch.current);
  }, [consumeBufferEffect, secondaryData, includeAssetFilters]);

  const primarySearchBuffer = useRef<IndexBuffer | null>(null);
  const secondarySearchBuffer = useRef<IndexBuffer | null>(null);

  const initialize = useCallback(() => {
    fetchPrimaryData();
    fetchSecondaryData();
  }, [fetchPrimaryData, fetchSecondaryData]);

  const searchIndex = useCallback(
    (
      index: React.MutableRefObject<WorkerSearchResult | null>,
      indexBuffer: React.MutableRefObject<IndexBuffer | null>,
      query: string,
    ): Promise<QueryResponse> => {
      return new Promise(async (res) => {
        if (index.current) {
          const result = await index.current.search(query);
          res(result);
        } else {
          // The user made a query before data is available
          // let's store the query in a buffer and once the data is available
          // we will consume the buffer
          if (indexBuffer.current) {
            // If the user changes the query before the data is available
            // lets "cancel" the last buffer (resolve its awaitable with
            // an empty response so it doesn't wait for all eternity) and
            // only store the most recent query
            indexBuffer.current.cancel();
          }
          indexBuffer.current = {
            query,
            resolve(response: QueryResponse) {
              res(response);
            },
            cancel() {
              res(EMPTY_RESPONSE);
            },
          };
        }
      });
    },
    [],
  );

  const searchPrimary = useCallback(
    async (queryString: string) => {
      return searchIndex(primarySearch, primarySearchBuffer, queryString);
    },
    [searchIndex],
  );

  const searchSecondary = useCallback(
    async (queryString: string) => {
      return searchIndex(secondarySearch, secondarySearchBuffer, queryString);
    },
    [searchIndex],
  );

  // Terminate the workers. Be careful with this: for users with very large workspaces, we should
  // avoid constantly re-querying and restarting the threads. It should only be used when we know
  // that there is fresh data to repopulate search.
  const terminate = useCallback(() => {
    primarySearch.current?.terminate();
    primarySearch.current = null;
    secondarySearch.current?.terminate();
    secondarySearch.current = null;
  }, []);

  return {
    initialize,
    loading: primaryDataLoading || secondaryDataLoading,
    searchPrimary,
    searchSecondary,
    terminate,
  };
};

export const SEARCH_PRIMARY_QUERY = gql`
  query SearchPrimaryQuery {
    workspaceOrError {
      ... on Workspace {
        id
        locationEntries {
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
                  assetGroups {
                    id
                    groupName
                  }
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
                  allTopLevelResourceDetails {
                    id
                    name
                  }
                }
              }
            }
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

export const SEARCH_SECONDARY_QUERY = gql`
  query SearchSecondaryQuery {
    assetsOrError {
      ... on AssetConnection {
        nodes {
          id
          key {
            path
          }
          definition {
            id
            computeKind
            groupName
            owners {
              ... on TeamAssetOwner {
                team
              }
              ... on UserAssetOwner {
                email
              }
            }
            repository {
              id
              name
              location {
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
