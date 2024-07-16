import isEqual from 'lodash/isEqual';
import {SetStateAction, useCallback, useMemo} from 'react';

import {buildAssetGroupSelector} from './AssetGroupSuggest';
import {isCanonicalStorageKindTag} from '../graph/KindTags';
import {
  AssetGroupSelector,
  AssetNode,
  AssetOwner,
  ChangeReason,
  DefinitionTag,
} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {doesFilterArrayMatchValueArray} from '../ui/Filters/useAssetTagFilter';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';

export type FilterableAssetDefinition = Partial<
  Pick<AssetNode, 'changedReasons' | 'owners' | 'groupName' | 'tags' | 'computeKind'> & {
    repository: Pick<AssetNode['repository'], 'name'> & {
      location: Pick<AssetNode['repository']['location'], 'name'>;
    };
  }
>;

export type AssetFilterBaseType = {
  groups: AssetGroupSelector[];
  computeKindTags: string[];
  storageKindTags: DefinitionTag[];
  changedInBranch: ChangeReason[];
  owners: AssetOwner[];
  tags: DefinitionTag[];
  repos: RepoAddress[];
};

export type AssetFilterType = AssetFilterBaseType & {
  selectAllFilters: Array<keyof AssetFilterBaseType>;
};

export const useAssetDefinitionFilterState = () => {
  const [filters, setFilters] = useQueryPersistedState<AssetFilterType>({
    encode: ({
      groups,
      computeKindTags,
      storageKindTags,
      changedInBranch,
      owners,
      tags,
      repos,
      selectAllFilters,
    }) => ({
      groups: groups?.length ? JSON.stringify(groups) : undefined,
      computeKindTags: computeKindTags?.length ? JSON.stringify(computeKindTags) : undefined,
      storageKindTags: storageKindTags?.length ? JSON.stringify(storageKindTags) : undefined,
      changedInBranch: changedInBranch?.length ? JSON.stringify(changedInBranch) : undefined,
      owners: owners?.length ? JSON.stringify(owners) : undefined,
      tags: tags?.length ? JSON.stringify(tags) : undefined,
      repos: repos?.length ? JSON.stringify(repos) : undefined,
      selectAllFilters: selectAllFilters?.length ? JSON.stringify(selectAllFilters) : undefined,
    }),
    decode: (qs) => ({
      groups: qs.groups ? JSON.parse(qs.groups) : [],
      computeKindTags: qs.computeKindTags ? JSON.parse(qs.computeKindTags) : [],
      storageKindTags: qs.storageKindTags ? JSON.parse(qs.storageKindTags) : [],
      changedInBranch: qs.changedInBranch ? JSON.parse(qs.changedInBranch) : [],
      owners: qs.owners ? JSON.parse(qs.owners) : [],
      tags: qs.tags ? JSON.parse(qs.tags) : [],
      repos: qs.repos
        ? JSON.parse(qs.repos).map((repo: RepoAddress) =>
            buildRepoAddress(repo.name, repo.location),
          )
        : [],
      selectAllFilters: qs.selectAllFilters ? JSON.parse(qs.selectAllFilters) : [],
    }),
  });

  const filterFn = useCallback(
    (node: FilterableAssetDefinition) => filterAssetDefinition(filters, node),
    [filters],
  );

  const {
    setComputeKindTags,
    setStorageKindTags,
    setGroups,
    setChangedInBranch,
    setOwners,
    setAssetTags,
    setRepos,
    setSelectAllFilters,
  } = useMemo(() => {
    function makeSetter<T extends keyof AssetFilterType>(field: T) {
      return (value: SetStateAction<AssetFilterType[T]>) => {
        setFilters?.((filters) => ({
          ...filters,
          [field]: value instanceof Function ? value(filters[field]) : value,
        }));
      };
    }
    return {
      setComputeKindTags: makeSetter('computeKindTags'),
      setStorageKindTags: makeSetter('storageKindTags'),
      setGroups: makeSetter('groups'),
      setChangedInBranch: makeSetter('changedInBranch'),
      setOwners: makeSetter('owners'),
      setAssetTags: makeSetter('tags'),
      setRepos: makeSetter('repos'),
      setSelectAllFilters: makeSetter('selectAllFilters'),
    };
  }, [setFilters]);

  return {
    filters,
    setFilters,
    filterFn,
    setComputeKindTags,
    setStorageKindTags,
    setGroups,
    setChangedInBranch,
    setOwners,
    setAssetTags,
    setRepos,
    setSelectAllFilters,
  };
};

export type AssetFilterState = ReturnType<typeof useAssetDefinitionFilterState>;

export function filterAssetDefinition(
  filters: Partial<AssetFilterState['filters']>,
  definition?: FilterableAssetDefinition | null,
) {
  if (filters.repos?.length) {
    const isAllReposSelected = filters.selectAllFilters?.includes('repos');
    if (isAllReposSelected) {
      if (!definition?.repository) {
        return false;
      }
    } else if (
      !definition ||
      !definition.repository ||
      !filters.repos.some(
        (repo) =>
          repo.location === definition?.repository?.location.name &&
          repo.name === definition?.repository.name,
      )
    ) {
      return false;
    }
  }
  const isAllGroupsSelected = filters.selectAllFilters?.includes('groups');
  if (isAllGroupsSelected) {
    if (!definition?.groupName || !definition?.repository) {
      return false;
    }
  } else if (filters.groups?.length) {
    if (!definition) {
      return false;
    }
    const {groupName, repository} = definition;
    if (!groupName || !repository) {
      return false;
    }
    const nodeGroup = buildAssetGroupSelector({definition: {groupName, repository}});
    if (!filters.groups.some((g) => isEqual(g, nodeGroup))) {
      return false;
    }
  }

  const isAllComputeKindTagsSelected = filters.selectAllFilters?.includes('computeKindTags');
  if (isAllComputeKindTagsSelected) {
    if (!definition?.computeKind?.length) {
      return false;
    }
  } else if (filters.computeKindTags?.length) {
    const lowercased = new Set(filters.computeKindTags.map((c) => c.toLowerCase()));
    if (!definition?.computeKind || !lowercased.has(definition.computeKind.toLowerCase())) {
      return false;
    }
  }

  const isAllStorageKindTagsSelected = filters.selectAllFilters?.includes('storageKindTags');
  const storageKindTag = definition?.tags?.find(isCanonicalStorageKindTag);
  if (isAllStorageKindTagsSelected) {
    if (!storageKindTag) {
      return false;
    }
  } else if (filters.storageKindTags?.length) {
    if (
      !storageKindTag ||
      !doesFilterArrayMatchValueArray(filters.storageKindTags, [storageKindTag])
    ) {
      return false;
    }
  }

  const isAllChangedInBranchSelected = filters.selectAllFilters?.includes('changedInBranch');
  if (isAllChangedInBranchSelected) {
    if (!definition?.changedReasons?.length) {
      return false;
    }
  } else if (filters.changedInBranch?.length || isAllChangedInBranchSelected) {
    if (
      !definition?.changedReasons?.length ||
      !definition.changedReasons.find((reason) => filters.changedInBranch!.includes(reason))
    ) {
      return false;
    }
  }
  const isAllOwnersSelected = filters.selectAllFilters?.includes('owners');
  if (isAllOwnersSelected) {
    if (!definition?.owners?.length) {
      return false;
    }
  } else if (filters.owners?.length) {
    if (
      !definition?.owners?.length ||
      !filters.owners.some((owner) =>
        definition.owners!.some((defOwner) => isEqual(defOwner, owner)),
      )
    ) {
      return false;
    }
  }
  const isAllTagsSelected = filters.selectAllFilters?.includes('tags');
  if (isAllTagsSelected) {
    if (!definition?.tags?.length) {
      return false;
    }
  } else if (filters.tags?.length) {
    if (
      !definition?.tags?.length ||
      !doesFilterArrayMatchValueArray(filters.tags, definition.tags)
    ) {
      return false;
    }
  }

  return true;
}
