import qs from 'qs';

import {GroupMetadata} from './BuildAssetSearchResults';
import {AssetOwner, DefinitionTag} from '../graphql/types';
import {repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

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
