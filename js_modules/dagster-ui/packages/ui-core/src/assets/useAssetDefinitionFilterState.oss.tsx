import isEqual from 'lodash/isEqual';
import {SetStateAction, useCallback, useMemo} from 'react';

import {buildAssetGroupSelector} from './AssetGroupSuggest';
import {
  AssetGroupSelector,
  AssetNode,
  AssetOwner,
  ChangeReason,
  DefinitionTag,
} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {doesFilterArrayMatchValueArray} from '../ui/Filters/doesFilterArrayMatchValueArray';
import {Tag} from '../ui/Filters/useDefinitionTagFilter';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';

type Nullable<T> = {
  [P in keyof T]: T[P] | null;
};

export type FilterableAssetDefinition = Nullable<
  Partial<
    Pick<AssetNode, 'changedReasons' | 'owners' | 'groupName' | 'tags' | 'kinds'> & {
      repository: Pick<AssetNode['repository'], 'name'> & {
        location: Pick<AssetNode['repository']['location'], 'name'>;
      };
    }
  >
>;

export type AssetFilterBaseType = {
  groups: AssetGroupSelector[];
  kinds: string[];
  changedInBranch: ChangeReason[];
  owners: AssetOwner[];
  tags: Omit<DefinitionTag, '__typename'>[];
  codeLocations: RepoAddress[];
};

export type AssetFilterType = AssetFilterBaseType & {
  selectAllFilters: Array<keyof AssetFilterBaseType>;
};

export const useAssetDefinitionFilterState = ({isEnabled = true}: {isEnabled?: boolean}) => {
  const [filters, setFilters] = useQueryPersistedState<AssetFilterType>({
    encode: isEnabled
      ? ({groups, kinds, changedInBranch, owners, tags, codeLocations, selectAllFilters}) => ({
          groups: groups?.length ? JSON.stringify(groups) : undefined,
          kinds: kinds?.length ? JSON.stringify(kinds) : undefined,
          changedInBranch: changedInBranch?.length ? JSON.stringify(changedInBranch) : undefined,
          owners: owners?.length ? JSON.stringify(owners) : undefined,
          tags: tags?.length ? JSON.stringify(tags) : undefined,
          codeLocations: codeLocations?.length ? JSON.stringify(codeLocations) : undefined,
          selectAllFilters: selectAllFilters?.length ? JSON.stringify(selectAllFilters) : undefined,
        })
      : () => ({}),
    decode: (qs) => ({
      groups: qs.groups && isEnabled ? JSON.parse(qs.groups) : [],
      kinds: qs.kinds && isEnabled ? JSON.parse(qs.kinds) : [],
      changedInBranch: qs.changedInBranch && isEnabled ? JSON.parse(qs.changedInBranch) : [],
      owners: qs.owners && isEnabled ? JSON.parse(qs.owners) : [],
      tags: qs.tags && isEnabled ? JSON.parse(qs.tags) : [],
      codeLocations:
        qs.codeLocations && isEnabled
          ? JSON.parse(qs.codeLocations).map((repo: RepoAddress) =>
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
    setKinds,
    setGroups,
    setChangedInBranch,
    setOwners,
    setAssetTags,
    setCodeLocations,
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
      setKinds: makeSetter('kinds'),
      setGroups: makeSetter('groups'),
      setChangedInBranch: makeSetter('changedInBranch'),
      setOwners: makeSetter('owners'),
      setAssetTags: makeSetter('tags'),
      setCodeLocations: makeSetter('codeLocations'),
      setSelectAllFilters: makeSetter('selectAllFilters'),
    };
  }, [setFilters]);

  return {
    filters,
    setFilters,
    filterFn,
    setKinds,
    setGroups,
    setChangedInBranch,
    setOwners,
    setAssetTags,
    setCodeLocations,
    setSelectAllFilters,
  };
};

export type AssetFilterState = ReturnType<typeof useAssetDefinitionFilterState>;

export function filterAssetDefinition(
  filters: Partial<AssetFilterState['filters']>,
  definition?: FilterableAssetDefinition | null,
) {
  if (filters.codeLocations?.length) {
    const isAllReposSelected = filters.selectAllFilters?.includes('codeLocations');
    if (isAllReposSelected) {
      if (!definition?.repository) {
        return false;
      }
    } else if (
      !definition ||
      !definition.repository ||
      !filters.codeLocations.some(
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
    if (
      !filters.groups.some((g) => {
        return (
          g.groupName.toLowerCase() === nodeGroup?.groupName.toLowerCase() &&
          g.repositoryLocationName === nodeGroup.repositoryLocationName &&
          g.repositoryName === nodeGroup.repositoryName
        );
      })
    ) {
      return false;
    }
  }

  const isAllKindsSelected = filters.selectAllFilters?.includes('kinds');
  const kinds = definition?.kinds;
  if (isAllKindsSelected) {
    if (!kinds) {
      return false;
    }
  } else if (filters.kinds?.length) {
    if (
      !kinds ||
      !doesFilterArrayMatchValueArray(
        filters.kinds.map((kind) => kind.toLowerCase()),
        kinds.map((kind) => kind.toLowerCase()),
      )
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
        definition.owners!.some((defOwner) =>
          isEqual(lowerCaseOwner(defOwner), lowerCaseOwner(owner)),
        ),
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
      !doesFilterArrayMatchValueArray(
        filters.tags.map(lowerCaseTag),
        definition.tags.map(lowerCaseTag),
      )
    ) {
      return false;
    }
  }

  return true;
}

const KEYS: Record<keyof AssetFilterType | 'asset-selection', '1'> = {
  groups: '1',
  kinds: '1',
  changedInBranch: '1',
  owners: '1',
  tags: '1',
  codeLocations: '1',
  'asset-selection': '1',
  selectAllFilters: '1',
};
export function getAssetFilterStateQueryString(search: string = location.search) {
  const params = new URLSearchParams(search);
  return Object.keys(KEYS).reduce((soFar, key) => {
    if (params.get(key)) {
      return soFar + `&${key}=${params.get(key)}`;
    }
    return soFar;
  }, '');
}

function lowerCaseOwner(owner: AssetOwner) {
  if (owner.__typename === 'TeamAssetOwner') {
    return {
      ...owner,
      team: owner.team.toLowerCase(),
    };
  } else {
    return {
      ...owner,
      email: owner.email.toLowerCase(),
    };
  }
}

function lowerCaseTag(tag: Tag) {
  return {
    ...tag,
    key: tag.key.toLowerCase(),
    value: tag.value?.toLowerCase(),
  };
}
