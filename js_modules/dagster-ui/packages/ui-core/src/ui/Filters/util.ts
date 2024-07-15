import {
  getStringValue as getStringValueAssetGroup,
  renderLabel as renderLabelAssetGroup,
} from './useAssetGroupFilter';
import {
  getStringValue as getStringValueAssetOwner,
  renderLabel as renderLabelAssetOwner,
} from './useAssetOwnerFilter';
import {
  getStringValue as getStringValueAssetTag,
  renderLabel as renderLabelAssetTag,
} from './useAssetTagFilter';
import {
  getStringValue as getStringValueChanged,
  renderLabel as renderLabelChanged,
} from './useChangedFilter';
import {
  getStringValue as getStringValueCodeLocation,
  renderLabel as renderLabelCodeLocation,
} from './useCodeLocationFilter';
import {
  getStringValue as getStringValueComputeKind,
  renderLabel as renderLabelComputeKind,
} from './useComputeKindTagFilter';
import {
  getStringValue as getStringValueStorageKind,
  renderLabel as renderLabelStorageKind,
} from './useStorageKindFilter';
import {AssetGroupSelector, AssetOwner, ChangeReason, DefinitionTag} from '../../graphql/types';
import {RepoAddress} from '../../workspace/types';
import {FilterArgs} from '../BaseFilters/useStaticSetFilter';

type Config<T> = Pick<FilterArgs<T>, 'getStringValue' | 'renderLabel' | 'getTooltipText'>;

export const CONFIG: {
  groups: Config<AssetGroupSelector>;
  computeKindTags: Config<string>;
  storageKindTags: Config<DefinitionTag>;
  changedInBranch: Config<ChangeReason>;
  owners: Config<AssetOwner>;
  tags: Config<DefinitionTag>;
  repos: Config<RepoAddress>;
} = {
  groups: {
    getStringValue: getStringValueAssetGroup,
    renderLabel: renderLabelAssetGroup,
  },
  computeKindTags: {
    getStringValue: getStringValueComputeKind,
    renderLabel: renderLabelComputeKind,
  },
  storageKindTags: {
    getStringValue: getStringValueStorageKind,
    renderLabel: renderLabelStorageKind,
  },
  changedInBranch: {
    getStringValue: getStringValueChanged,
    renderLabel: renderLabelChanged,
  },
  owners: {
    getStringValue: getStringValueAssetOwner,
    renderLabel: renderLabelAssetOwner,
  },
  tags: {
    getStringValue: getStringValueAssetTag,
    renderLabel: renderLabelAssetTag,
  },
  repos: {
    getStringValue: getStringValueCodeLocation,
    renderLabel: renderLabelCodeLocation,
  },
};
