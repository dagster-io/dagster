import {BaseConfig as AssetGroupsFilterBaseConfig} from './useAssetGroupFilter';
import {BaseConfig as AssetOwnerFilterBaseConfig} from './useAssetOwnerFilter';
import {BaseConfig as AssetTagFilterBaseConfig} from './useAssetTagFilter';
import {BaseConfig as ChangedFilterBaseConfig} from './useChangedFilter';
import {BaseConfig as CodeLocationFilterBaseConfig} from './useCodeLocationFilter';
import {BaseConfig as KindFilterBaseConfig} from './useKindFilter';
import {AssetGroupSelector, AssetOwner, ChangeReason, DefinitionTag} from '../../graphql/types';
import {RepoAddress} from '../../workspace/types';
import {StaticBaseConfig} from '../BaseFilters/useStaticSetFilter';

export const STATIC_FILTER_CONFIGS: {
  groups: StaticBaseConfig<AssetGroupSelector>;
  kinds: StaticBaseConfig<string>;
  changedInBranch: StaticBaseConfig<ChangeReason>;
  owners: StaticBaseConfig<AssetOwner>;
  tags: StaticBaseConfig<DefinitionTag>;
  codeLocations: StaticBaseConfig<RepoAddress>;
} = {
  groups: AssetGroupsFilterBaseConfig,
  kinds: KindFilterBaseConfig,
  changedInBranch: ChangedFilterBaseConfig,
  owners: AssetOwnerFilterBaseConfig,
  tags: AssetTagFilterBaseConfig,
  codeLocations: CodeLocationFilterBaseConfig,
};
