import {useCallback, useContext, useEffect, useRef} from 'react';
import {useAugmentSearchResults} from 'shared/search/useAugmentSearchResults.oss';

import {buildAssetCountBySection} from './BuildAssetSearchResults';
import {QueryResponse, WorkerSearchResult, createSearchWorker} from './createSearchWorker';
import {
  linkToAssetTableWithAssetOwnerFilter,
  linkToAssetTableWithGroupFilter,
  linkToAssetTableWithKindFilter,
  linkToAssetTableWithTagFilter,
  linkToCodeLocation,
} from './links';
import {AssetFilterSearchResultType, SearchResult, SearchResultType} from './types';
import {useShowAssetsWithoutDefinitions} from '../app/UserSettingsDialog/useShowAssetsWithoutDefinitions';
import {useShowStubAssets} from '../app/UserSettingsDialog/useShowStubAssets';
import {useFeatureFlags} from '../app/useFeatureFlags';
import {displayNameForAssetKey, isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {globalAssetGraphPathToString} from '../assets/globalAssetGraphPathToString';
import {AssetTableFragment} from '../assets/types/AssetTableFragment.types';
import {useAllAssets} from '../assets/useAllAssets';
import {buildTagString} from '../ui/tagAsString';
import {WorkspaceContext, WorkspaceState} from '../workspace/WorkspaceContext/WorkspaceContext';
import {assetOwnerAsString} from '../workspace/assetOwnerAsString';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';
import {workspacePath} from '../workspace/workspacePath';

const primaryDataToSearchResults = (
  locationEntries: WorkspaceState['locationEntries'],
  flagAssetGraphGroupsPerCodeLocation: boolean,
) => {
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
              description:
                manyLocations && flagAssetGraphGroupsPerCodeLocation
                  ? `Asset group in ${repoPath}`
                  : 'Asset group',
              node: assetGroup,
              href: flagAssetGraphGroupsPerCodeLocation
                ? workspacePath(repoName, locationName, `/asset-groups/${groupName}`)
                : globalAssetGraphPathToString({opsQuery: `group:"${groupName}"`, opNames: []}),
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
  assets: AssetTableFragment[],
  searchContext: 'global' | 'catalog',
) => {
  if (!assets || assets.length === 0) {
    return [];
  }

  const nodes = assets.filter(({definition}) => {
    if (definition === null) {
      return false;
    }
    return true;
  });

  const assetResults: SearchResult[] = nodes.map((node) => ({
    key: node.key,
    label: displayNameForAssetKey(node.key),
    description: `Asset in ${buildRepoPathForHuman(
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      node.definition!.repository.name,
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      node.definition!.repository.location.name,
    )}`,
    node,
    href: assetDetailsPathForKey(node.key),
    type: SearchResultType.Asset,
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    tags: node.definition!.tags,
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    kinds: node.definition!.kinds,
  }));

  if (searchContext === 'global') {
    return [...assetResults];
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
      ...assetResults,
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
  includeScore: true,

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

  const {locationEntries, loadingNonAssets} = useContext(WorkspaceContext);

  const {assets: _assets, loading: assetsLoading} = useAllAssets();
  const {showAssetsWithoutDefinitions} = useShowAssetsWithoutDefinitions();
  const {flagAssetGraphGroupsPerCodeLocation} = useFeatureFlags();

  const {showStubAssets} = useShowStubAssets();
  const assets = _assets.filter((asset) => {
    if (!showStubAssets && asset.definition?.isAutoCreatedStub) {
      return false;
    }
    if (!showAssetsWithoutDefinitions && !asset.definition) {
      return false;
    }
    return true;
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
    if (loadingNonAssets) {
      return;
    }
    const results = primaryDataToSearchResults(
      locationEntries,
      flagAssetGraphGroupsPerCodeLocation,
    );
    const augmentedResults = augmentSearchResults(results);
    if (!primarySearch.current) {
      primarySearch.current = createSearchWorker('primary', fuseOptions);
    }
    primarySearch.current.update(augmentedResults);
    consumeBufferEffect(primarySearchBuffer, primarySearch.current);
  }, [
    consumeBufferEffect,
    locationEntries,
    augmentSearchResults,
    loadingNonAssets,
    flagAssetGraphGroupsPerCodeLocation,
  ]);

  useEffect(() => {
    if (assetsLoading) {
      return;
    }

    const results = secondaryDataToSearchResults(assets, searchContext);
    const augmentedResults = augmentSearchResults(results);
    if (!secondarySearch.current) {
      secondarySearch.current = createSearchWorker('secondary', fuseOptions);
    }
    secondarySearch.current.update(augmentedResults);
    consumeBufferEffect(secondarySearchBuffer, secondarySearch.current);
  }, [consumeBufferEffect, assets, searchContext, augmentSearchResults, assetsLoading]);

  const primarySearchBuffer = useRef<IndexBuffer | null>(null);
  const secondarySearchBuffer = useRef<IndexBuffer | null>(null);

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
    loading: assetsLoading || loadingNonAssets,
    searchPrimary,
    searchSecondary,
    terminate,
  };
};
