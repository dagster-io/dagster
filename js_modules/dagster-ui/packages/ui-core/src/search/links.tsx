import qs from 'qs';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {GroupMetadata} from './BuildAssetSearchResults';
import {featureEnabled} from '../app/Flags';
import {AssetOwner, DefinitionTag} from '../graphql/types';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';
import {repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

export const linkToAssetTableWithGroupFilter = (groupMetadata: GroupMetadata) => {
  if (featureEnabled(FeatureFlag.flagSelectionSyntax)) {
    return `/assets?${qs.stringify({
      'asset-selection': `group:"${groupMetadata.groupName}" and code_location:"${buildRepoPathForHuman(groupMetadata.repositoryName, groupMetadata.repositoryLocationName)}"`,
    })}`;
  }
  return `/assets?${qs.stringify({groups: JSON.stringify([groupMetadata])})}`;
};

export const linkToAssetTableWithKindFilter = (kind: string) => {
  if (featureEnabled(FeatureFlag.flagSelectionSyntax)) {
    return `/assets?${qs.stringify({
      'asset-selection': `kind:"${kind}"`,
    })}`;
  }
  return `/assets?${qs.stringify({
    kinds: JSON.stringify([kind]),
  })}`;
};

export const linkToAssetTableWithTagFilter = (tag: Omit<DefinitionTag, '__typename'>) => {
  if (featureEnabled(FeatureFlag.flagSelectionSyntax)) {
    return `/assets?${qs.stringify({
      'asset-selection': `tag:"${tag.key}"${tag.value ? `="${tag.value}"` : ''}`,
    })}`;
  }
  return `/assets?${qs.stringify({
    tags: JSON.stringify([tag]),
  })}`;
};

export const linkToAssetTableWithAssetOwnerFilter = (owner: AssetOwner) => {
  if (featureEnabled(FeatureFlag.flagSelectionSyntax)) {
    return `/assets?${qs.stringify({
      'asset-selection': `owner:"${owner.__typename === 'TeamAssetOwner' ? owner.team : owner.email}"`,
    })}`;
  }
  return `/assets?${qs.stringify({
    owners: JSON.stringify([owner]),
  })}`;
};

export const linkToAssetTableWithColumnsFilter = (columns: string[]) => {
  if (featureEnabled(FeatureFlag.flagSelectionSyntax)) {
    return `/assets?${qs.stringify({
      'asset-selection': columns.map((column) => `column:"${column}"`).join(' or '),
    })}`;
  }
  return `/assets?${qs.stringify({
    columns: JSON.stringify(columns),
  })}`;
};

export const linkToAssetTableWithColumnTagFilter = (tag: Omit<DefinitionTag, '__typename'>) => {
  if (featureEnabled(FeatureFlag.flagSelectionSyntax)) {
    return `/assets?${qs.stringify({
      'asset-selection': `column_tag:"${tag.key}"${tag.value ? `="${tag.value}"` : ''}`,
    })}`;
  }
  return `/assets?${qs.stringify({
    columnTags: JSON.stringify([tag]),
  })}`;
};

export const linkToCodeLocation = (repoAddress: RepoAddress) => {
  return `/locations/${repoAddressAsURLString(repoAddress)}/assets`;
};

export const linkToAssetTableWithTableNameFilter = (tableName: string) => {
  if (featureEnabled(FeatureFlag.flagSelectionSyntax)) {
    return `/assets?${qs.stringify({
      'asset-selection': `table_name:"${tableName}"`,
    })}`;
  }
  return `/assets?${qs.stringify({
    tableNames: JSON.stringify([tableName]),
  })}`;
};
