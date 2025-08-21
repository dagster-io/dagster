import {IconName} from '@dagster-io/ui-components';
import {observeEnabled} from 'shared/app/observeEnabled.oss';

import {assertUnreachable} from '../../app/Util';
import {AssetGraphQueryItem} from '../../asset-graph/types';
import {isKindTag} from '../../graph/KindTags';
import {AssetHealthStatus} from '../../graphql/types';
import {weakMapMemoize} from '../../util/weakMapMemoize';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';

export const getAttributesMap = (assets: AssetGraphQueryItem[]) => {
  const assetNamesSet: Set<string> = new Set();
  const seenTags: Set<string> = new Set();
  const tagSet: Set<{key: string; value: string}> = new Set();
  const ownersSet: Set<string> = new Set();
  const groupsSet: Set<string> = new Set();
  const kindsSet: Set<string> = new Set();
  const codeLocationSet: Set<string> = new Set();

  assets.forEach((asset) => {
    assetNamesSet.add(asset.name);
    if (asset.node.tags.length > 0) {
      asset.node.tags.forEach((tag) => {
        if (isKindTag(tag)) {
          return;
        }
        if (seenTags.has(JSON.stringify(tag))) {
          return;
        }
        tagSet.add(memoizedTag(tag.key, tag.value));
      });
    }
    if (asset.node.owners.length > 0) {
      asset.node.owners.forEach((owner) => {
        switch (owner.__typename) {
          case 'TeamAssetOwner':
            ownersSet.add(owner.team);
            break;
          case 'UserAssetOwner':
            ownersSet.add(owner.email);
            break;
          default:
            assertUnreachable(owner);
        }
      });
    } else {
      ownersSet.add('');
    }
    if (asset.node.groupName) {
      groupsSet.add(asset.node.groupName);
    } else {
      groupsSet.add('');
    }
    if (asset.node.kinds.length > 0) {
      asset.node.kinds.forEach((kind) => {
        kindsSet.add(kind);
      });
    } else {
      kindsSet.add('');
    }
    const repository = asset.node.repository;
    if (repository && repository.location.name && repository.name) {
      const location = buildRepoPathForHuman(repository.name, repository.location.name);
      codeLocationSet.add(location);
    } else {
      codeLocationSet.add('');
    }
  });

  const assetNames = Array.from(assetNamesSet).sort();
  const tagNames = Array.from(tagSet).sort();
  const owners = Array.from(ownersSet).sort();
  const groups = Array.from(groupsSet).sort();
  const kinds = Array.from(kindsSet).sort();
  const codeLocations = Array.from(codeLocationSet).sort();
  const data = {
    key: assetNames,
    tag: tagNames,
    owner: owners,
    group: groups,
    kind: kinds,
    code_location: codeLocations,
  };
  if (observeEnabled()) {
    const statuses = [
      AssetHealthStatus.HEALTHY,
      AssetHealthStatus.DEGRADED,
      AssetHealthStatus.WARNING,
      AssetHealthStatus.UNKNOWN,
      AssetHealthStatus.NOT_APPLICABLE,
      ...SUB_STATUSES,
    ];
    return {
      ...data,
      status: statuses,
    };
  }
  return data;
};

export const memoizedTag = weakMapMemoize((key: string, value: string) => ({
  key,
  value,
}));

export type Attribute = keyof ReturnType<typeof getAttributesMap> | 'status';

export const attributeToIcon: Record<Attribute, IconName> = {
  key: 'magnify_glass',
  kind: 'compute_kind',
  code_location: 'code_location',
  group: 'asset_group',
  owner: 'owner',
  tag: 'tag',
  status: 'status',
};

export const assetSelectionSyntaxSupportedAttributes: Attribute[] = Object.keys(
  attributeToIcon,
) as Attribute[];

export const unsupportedAttributeMessages = {
  column_tag: 'column_tag filtering is available in Dagster+',
  column: 'column filtering is available in Dagster+',
  table_name: 'table_name filtering is available in Dagster+',
  changed_in_branch: 'changed_in_branch filtering is available in Dagster+ branch deployments',
  status: 'status filtering is available in Dagster+',
};

export const SUB_STATUSES = [
  'MATERIALIZATION_SUCCESS',
  'MATERIALIZATION_FAILURE',
  'MATERIALIZATION_UNKNOWN',
  'CHECK_PASSED',
  'CHECK_WARNING',
  'CHECK_ERROR',
  'CHECK_EXECUTION_FAILED',
  'CHECK_UNKNOWN',
  'CHECK_MISSING',
  'FRESHNESS_PASSING',
  'FRESHNESS_WARNING',
  'FRESHNESS_FAILURE',
  'FRESHNESS_UNKNOWN',
  'FRESHNESS_MISSING',
] as const;
