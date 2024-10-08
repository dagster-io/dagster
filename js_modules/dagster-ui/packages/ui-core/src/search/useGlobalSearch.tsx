import qs from 'qs';
import {useCallback, useContext, useEffect, useRef} from 'react';
import {useAugmentSearchResults} from 'shared/search/useAugmentSearchResults.oss';

import {GroupMetadata, buildAssetCountBySection} from './BuildAssetSearchResults';
import {QueryResponse, WorkerSearchResult, createSearchWorker} from './createSearchWorker';
import {AssetFilterSearchResultType, SearchResult, SearchResultType} from './types';
import {
  SearchPrimaryQuery,
  SearchPrimaryQueryVariables,
  SearchPrimaryQueryVersion,
  SearchSecondaryQuery,
  SearchSecondaryQueryVariables,
  SearchSecondaryQueryVersion,
} from './types/useGlobalSearch.types';
import {useIndexedDBCachedQuery} from './useIndexedDBCachedQuery';
import {gql} from '../apollo-client';
import {AppContext} from '../app/AppContext';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {displayNameForAssetKey, isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetOwner, DefinitionTag} from '../graphql/types';
import {buildTagString} from '../ui/tagAsString';
import {assetOwnerAsString} from '../workspace/assetOwnerAsString';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';
import {repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePath} from '../workspace/workspacePath';

export const linkToAssetTableWithGroupFilter = (groupMetadata: GroupMetadata) => {
  return `/assets?${qs.stringify({groups: JSON.stringify([groupMetadata])})}`;
};

export const linkToAssetTableWithKindFilter = (kind: string) => {
  return `/assets?${qs.stringify({
    kinds: JSON.stringify([kind]),
  })}`;
};

export const linkToAssetTableWithTagFilter = (tag: Omit<DefinitionTag, '__typename'>) => {
  return `/assets?${qs.stringify({
    tags: JSON.stringify([tag]),
  })}`;
};

export const linkToAssetTableWithAssetOwnerFilter = (owner: AssetOwner) => {
  return `/assets?${qs.stringify({
    owners: JSON.stringify([owner]),
  })}`;
};

export const linkToAssetTableWithColumnsFilter = (columns: string[]) => {
  return `/assets?${qs.stringify({
    columns: JSON.stringify(columns),
  })}`;
};

export const linkToAssetTableWithColumnTagFilter = (tag: Omit<DefinitionTag, '__typename'>) => {
  return `/assets?${qs.stringify({
    columnTags: JSON.stringify([tag]),
  })}`;
};

export const linkToCodeLocation = (repoAddress: RepoAddress) => {
  return `/locations/${repoAddressAsURLString(repoAddress)}/assets`;
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
    accum.push(
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
              node: assetGroup,
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
                node: pipelineOrJob,
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
          node: schedule,
          description: manyLocations ? `Schedule in ${repoPath}` : 'Schedule',
          href: workspacePath(repoName, locationName, `/schedules/${schedule.name}`),
          type: SearchResultType.Schedule,
        }));

        const allSensors: SearchResult[] = sensors.map((sensor) => ({
          label: sensor.name,
          node: sensor,
          description: manyLocations ? `Sensor in ${repoPath}` : 'Sensor',
          href: workspacePath(repoName, locationName, `/sensors/${sensor.name}`),
          type: SearchResultType.Sensor,
        }));

        const allResources: SearchResult[] = allTopLevelResourceDetails.map((resource) => ({
          label: resource.name,
          node: resource,
          description: manyLocations ? `Resource in ${repoPath}` : 'Resource',
          href: workspacePath(repoName, locationName, `/resources/${resource.name}`),
          type: SearchResultType.Resource,
        }));

        const allPartitionSets: SearchResult[] = partitionSets
          .filter((item) => !isHiddenAssetGroupJob(item.pipelineName))
          .map((partitionSet) => ({
            label: partitionSet.name,
            node: partitionSet,
            description: manyLocations ? `Partition set in ${repoPath}` : 'Partition set',
            href: workspacePath(
              repoName,
              locationName,
              `/pipeline_or_job/${partitionSet.pipelineName}/partitions?partitionSet=${partitionSet.name}`,
            ),
            type: SearchResultType.PartitionSet,
          }));

        inner.push(...allAssetGroups);
        inner.push(...allPipelinesAndJobs);
        inner.push(...allSchedules);
        inner.push(...allSensors);
        inner.push(...allPartitionSets);
        inner.push(...allResources);

        return inner;
      }, [] as SearchResult[]),
    );
    return accum;
  }, [] as SearchResult[]);

  return allEntries;
};

const secondaryDataToSearchResults = (
  input: {data?: SearchSecondaryQuery},
  searchContext: 'global' | 'catalog',
) => {
  const {data} = input;
  if (!data?.assetsOrError || data.assetsOrError.__typename === 'PythonError') {
    return [];
  }

  const {nodes} = data.assetsOrError;

  const assets: SearchResult[] = nodes
    .filter(({definition}) => definition !== null)
    .map((node) => ({
      label: displayNameForAssetKey(node.key),
      description: `Asset in ${buildRepoPathForHuman(
        node.definition!.repository.name,
        node.definition!.repository.location.name,
      )}`,
      node,
      href: assetDetailsPathForKey(node.key),
      type: SearchResultType.Asset,
      tags: node.definition!.tags,
      kinds: node.definition!.kinds,
    }));

  if (searchContext === 'global') {
    return [...assets];
  } else {
    const countsBySection = buildAssetCountBySection(nodes);

    const kindResults: SearchResult[] = countsBySection.countsByKind.map(({kind, assetCount}) => ({
      label: kind,
      description: '',
      type: AssetFilterSearchResultType.Kind,
      href: linkToAssetTableWithKindFilter(kind),
      numResults: assetCount,
    }));

    const tagResults: SearchResult[] = countsBySection.countPerTag.map(({tag, assetCount}) => ({
      label: buildTagString(tag),
      description: '',
      type: AssetFilterSearchResultType.Tag,
      href: linkToAssetTableWithTagFilter(tag),
      numResults: assetCount,
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
        repoPath: buildRepoPathForHuman(
          groupAssetCount.groupMetadata.repositoryName,
          groupAssetCount.groupMetadata.repositoryLocationName,
        ),
      }),
    );

    const ownerResults: SearchResult[] = countsBySection.countsByOwner.map(
      ({owner, assetCount}) => ({
        label: assetOwnerAsString(owner),
        description: '',
        type: AssetFilterSearchResultType.Owner,
        href: linkToAssetTableWithAssetOwnerFilter(owner),
        numResults: assetCount,
      }),
    );
    return [
      ...assets,
      ...kindResults,
      ...tagResults,
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

  // Allow searching to continue to the end of the string.
  ignoreLocation: true,
};

const EMPTY_RESPONSE = {queryString: '', results: []};

type IndexBuffer = {
  query: string;
  resolve: (value: QueryResponse) => void;
  cancel: () => void;
};

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
export const useGlobalSearch = ({searchContext}: {searchContext: 'global' | 'catalog'}) => {
  const primarySearch = useRef<WorkerSearchResult | null>(null);
  const secondarySearch = useRef<WorkerSearchResult | null>(null);

  const augmentSearchResults = useAugmentSearchResults();

  const {localCacheIdPrefix} = useContext(AppContext);

  const {
    data: primaryData,
    fetch: fetchPrimaryData,
    loading: primaryDataLoading,
  } = useIndexedDBCachedQuery<SearchPrimaryQuery, SearchPrimaryQueryVariables>({
    query: SEARCH_PRIMARY_QUERY,
    key: `${localCacheIdPrefix}/SearchPrimary`,
    version: SearchPrimaryQueryVersion,
  });

  // Delete old database from before the prefix, remove this at some point
  indexedDB.deleteDatabase('indexdbQueryCache:SearchPrimary');

  const {
    data: secondaryData,
    fetch: fetchSecondaryData,
    loading: secondaryDataLoading,
  } = useIndexedDBCachedQuery<SearchSecondaryQuery, SearchSecondaryQueryVariables>({
    query: SEARCH_SECONDARY_QUERY,
    key: `${localCacheIdPrefix}/SearchSecondary`,
    version: SearchSecondaryQueryVersion,
  });

  // Delete old database from before the prefix, remove this at some point
  indexedDB.deleteDatabase('indexdbQueryCache:SearchSecondary');

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
    const augmentedResults = augmentSearchResults(results, searchContext);
    if (!primarySearch.current) {
      primarySearch.current = createSearchWorker('primary', fuseOptions);
    }
    primarySearch.current.update(augmentedResults);
    consumeBufferEffect(primarySearchBuffer, primarySearch.current);
  }, [consumeBufferEffect, primaryData, searchContext, augmentSearchResults]);

  useEffect(() => {
    if (!secondaryData) {
      return;
    }
    const results = secondaryDataToSearchResults({data: secondaryData}, searchContext);
    const augmentedResults = augmentSearchResults(results, searchContext);
    if (!secondarySearch.current) {
      secondarySearch.current = createSearchWorker('secondary', fuseOptions);
    }
    secondarySearch.current.update(augmentedResults);
    consumeBufferEffect(secondarySearchBuffer, secondarySearch.current);
  }, [consumeBufferEffect, secondaryData, searchContext, augmentSearchResults]);

  const primarySearchBuffer = useRef<IndexBuffer | null>(null);
  const secondarySearchBuffer = useRef<IndexBuffer | null>(null);

  const initialize = useCallback(() => {
    if (!primaryData && !primaryDataLoading) {
      fetchPrimaryData();
    }
    if (!secondaryData && !secondaryDataLoading) {
      fetchSecondaryData();
    }
  }, [
    fetchPrimaryData,
    fetchSecondaryData,
    primaryData,
    primaryDataLoading,
    secondaryData,
    secondaryDataLoading,
  ]);

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
                    ...SearchGroupFragment
                  }
                  pipelines {
                    id
                    ...SearchPipelineFragment
                  }
                  schedules {
                    id
                    ...SearchScheduleFragment
                  }
                  sensors {
                    id
                    ...SearchSensorFragment
                  }
                  partitionSets {
                    id
                    ...SearchPartitionSetFragment
                  }
                  allTopLevelResourceDetails {
                    id
                    ...SearchResourceDetailFragment
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

  fragment SearchGroupFragment on AssetGroup {
    id
    groupName
  }

  fragment SearchPipelineFragment on Pipeline {
    id
    isJob
    name
  }

  fragment SearchScheduleFragment on Schedule {
    id
    name
  }
  fragment SearchSensorFragment on Sensor {
    id
    name
  }
  fragment SearchPartitionSetFragment on PartitionSet {
    id
    name
    pipelineName
  }
  fragment SearchResourceDetailFragment on ResourceDetails {
    id
    name
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

export const SEARCH_SECONDARY_QUERY = gql`
  query SearchSecondaryQuery {
    assetsOrError {
      ... on AssetConnection {
        nodes {
          id
          ...SearchAssetFragment
        }
      }
    }
  }

  fragment SearchAssetFragment on Asset {
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
      tags {
        key
        value
      }
      kinds
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
`;
