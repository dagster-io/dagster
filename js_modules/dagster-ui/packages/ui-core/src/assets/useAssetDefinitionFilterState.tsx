import isEqual from 'lodash/isEqual';
import {useCallback, useMemo} from 'react';

import {buildAssetGroupSelector} from './AssetGroupSuggest';
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

type StrippedDownDefinition = Pick<
  AssetNode,
  'changedReasons' | 'owners' | 'groupName' | 'tags' | 'computeKind'
> & {
  repository: Pick<AssetNode['repository'], 'name'> & {
    location: Pick<AssetNode['repository']['location'], 'name'>;
  };
};

export type AssetFilterType = {
  groups: AssetGroupSelector[];
  computeKindTags: string[];
  changedInBranch: ChangeReason[];
  owners: AssetOwner[];
  tags: DefinitionTag[];
  repos: RepoAddress[];
};

export const useAssetDefinitionFilterState = () => {
  const [filters, setFilters] = useQueryPersistedState<AssetFilterType>({
    encode: ({groups, computeKindTags, changedInBranch, owners, tags, repos}) => ({
      groups: groups?.length ? JSON.stringify(groups) : undefined,
      computeKindTags: computeKindTags?.length ? JSON.stringify(computeKindTags) : undefined,
      changedInBranch: changedInBranch?.length ? JSON.stringify(changedInBranch) : undefined,
      owners: owners?.length ? JSON.stringify(owners) : undefined,
      tags: tags?.length ? JSON.stringify(tags) : undefined,
      repos: repos?.length ? JSON.stringify(repos) : undefined,
    }),
    decode: (qs) => ({
      groups: qs.groups ? JSON.parse(qs.groups) : [],
      computeKindTags: qs.computeKindTags ? JSON.parse(qs.computeKindTags) : [],
      changedInBranch: qs.changedInBranch ? JSON.parse(qs.changedInBranch) : [],
      owners: qs.owners ? JSON.parse(qs.owners) : [],
      tags: qs.tags ? JSON.parse(qs.tags) : [],
      repos: qs.repos
        ? JSON.parse(qs.repos).map((repo: RepoAddress) =>
            buildRepoAddress(repo.name, repo.location),
          )
        : [],
    }),
  });

  const filterFn = useCallback(
    (definition?: StrippedDownDefinition | null) => {
      if (filters.repos?.length) {
        if (
          !filters.repos.some(
            (repo) =>
              repo.location === definition?.repository.location.name &&
              repo.name === definition?.repository.name,
          )
        ) {
          return false;
        }
      }
      if (filters.groups?.length) {
        if (!definition) {
          return false;
        }
        const nodeGroup = buildAssetGroupSelector({definition});
        if (!filters.groups.some((g) => isEqual(g, nodeGroup))) {
          return false;
        }
      }

      if (filters.computeKindTags?.length) {
        if (!definition || !filters.computeKindTags.includes(definition.computeKind ?? '')) {
          return false;
        }
      }

      if (filters.changedInBranch?.length) {
        if (
          !definition ||
          definition.changedReasons.find((reason) => filters.changedInBranch!.includes(reason))
        ) {
          return false;
        }
      }
      if (filters.owners?.length) {
        if (
          !filters.owners.some((owner) =>
            definition?.owners.length
              ? definition.owners.some((defOwner) => isEqual(defOwner, owner))
              : false,
          )
        ) {
          return false;
        }
      }
      if (filters.tags?.length) {
        if (!doesFilterArrayMatchValueArray(filters.tags, definition?.tags ?? [])) {
          return false;
        }
      }

      return true;
    },
    [
      filters.repos,
      filters.groups,
      filters.changedInBranch,
      filters.computeKindTags,
      filters.owners,
      filters.tags,
    ],
  );

  const {setComputeKindTags, setGroups, setChangedInBranch, setOwners, setAssetTags, setRepos} =
    useMemo(() => {
      function makeSetter<T extends keyof AssetFilterType>(field: T) {
        return (value: AssetFilterType[T]) => {
          setFilters?.((filters) => ({
            ...filters,
            [field]: value,
          }));
        };
      }
      return {
        setComputeKindTags: makeSetter('computeKindTags'),
        setGroups: makeSetter('groups'),
        setChangedInBranch: makeSetter('changedInBranch'),
        setOwners: makeSetter('owners'),
        setAssetTags: makeSetter('tags'),
        setRepos: makeSetter('repos'),
      };
    }, [setFilters]);

  return {
    filters,
    setFilters,
    filterFn,
    setComputeKindTags,
    setGroups,
    setChangedInBranch,
    setOwners,
    setAssetTags,
    setRepos,
  };
};

export type AssetFilterState = ReturnType<typeof useAssetDefinitionFilterState>;
