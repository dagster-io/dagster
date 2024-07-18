import {BaseConfig as AssetGroupsFilterBaseConfig} from './useAssetGroupFilter';
import {BaseConfig as AssetOwnerFilterBaseConfig} from './useAssetOwnerFilter';
import {BaseConfig as AssetTagFilterBaseConfig} from './useAssetTagFilter';
import {BaseConfig as ChangedFilterBaseConfig} from './useChangedFilter';
import {BaseConfig as CodeLocationFilterBaseConfig} from './useCodeLocationFilter';
import {BaseConfig as ComputeKindTagFilterBaseConfig} from './useComputeKindTagFilter';
import {BaseConfig as StorageKindFilterBaseConfig} from './useStorageKindFilter';
import {AssetGroupSelector, AssetOwner, ChangeReason, DefinitionTag} from '../../graphql/types';
import {RepoAddress} from '../../workspace/types';
import {StaticBaseConfig} from '../BaseFilters/useStaticSetFilter';

export const STATIC_FILTER_CONFIGS: {
  groups: StaticBaseConfig<AssetGroupSelector>;
  computeKindTags: StaticBaseConfig<string>;
  storageKindTags: StaticBaseConfig<DefinitionTag>;
  changedInBranch: StaticBaseConfig<ChangeReason>;
  owners: StaticBaseConfig<AssetOwner>;
  tags: StaticBaseConfig<DefinitionTag>;
  repos: StaticBaseConfig<RepoAddress>;
} = {
  groups: AssetGroupsFilterBaseConfig,
  computeKindTags: ComputeKindTagFilterBaseConfig,
  storageKindTags: StorageKindFilterBaseConfig,
  changedInBranch: ChangedFilterBaseConfig,
  owners: AssetOwnerFilterBaseConfig,
  tags: AssetTagFilterBaseConfig,
  repos: CodeLocationFilterBaseConfig,
};
