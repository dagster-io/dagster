import qs from 'qs';

import {GroupMetadata} from './BuildAssetSearchResults';
import {AssetOwner, DefinitionTag} from '../graphql/types';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';
import {repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

export const linkToAssetTableWithGroupFilter = (groupMetadata: GroupMetadata) => {
  return `/assets?${qs.stringify({
    'asset-selection': `group:"${groupMetadata.groupName}" and code_location:"${buildRepoPathForHuman(groupMetadata.repositoryName, groupMetadata.repositoryLocationName)}"`,
  })}`;
};

export const linkToAssetTableWithCrossCodeLocationGroupFilter = (groupName: string) => {
  return `/assets?${qs.stringify({
    'asset-selection': `group:"${groupName}"`,
  })}`;
};

export const linkToAssetTableWithKindFilter = (kind: string) => {
  return `/assets?${qs.stringify({
    'asset-selection': `kind:"${kind}"`,
  })}`;
};

export const linkToAssetTableWithTagFilter = (tag: Omit<DefinitionTag, '__typename'>) => {
  return `/assets?${qs.stringify({
    'asset-selection': `tag:"${tag.key}"${tag.value ? `="${tag.value}"` : ''}`,
  })}`;
};

export const linkToAssetTableWithAssetOwnerFilter = (owner: AssetOwner) => {
  return `/assets?${qs.stringify({
    'asset-selection': `owner:"${owner.__typename === 'TeamAssetOwner' ? owner.team : owner.email}"`,
  })}`;
};

export const linkToAssetTableWithColumnsFilter = (columns: string[]) => {
  return `/assets?${qs.stringify({
    'asset-selection': columns.map((column) => `column:"${column}"`).join(' or '),
  })}`;
};

export const linkToAssetTableWithColumnTagFilter = (tag: Omit<DefinitionTag, '__typename'>) => {
  return `/assets?${qs.stringify({
    'asset-selection': `column_tag:"${tag.key}"${tag.value ? `="${tag.value}"` : ''}`,
  })}`;
};

export const linkToCodeLocation = (repoAddress: RepoAddress) => {
  return `/locations/${repoAddressAsURLString(repoAddress)}/assets`;
};

export const linkToCodeLocationInCatalog = (
  repositoryName: string,
  repositoryLocationName: string,
) => {
  return `/assets?${qs.stringify({
    'asset-selection': `code_location:"${buildRepoPathForHuman(repositoryName, repositoryLocationName)}"`,
  })}`;
};

export const linkToAssetTableWithTableNameFilter = (tableName: string) => {
  return `/assets?${qs.stringify({
    'asset-selection': `table_name:"${tableName}"`,
  })}`;
};
