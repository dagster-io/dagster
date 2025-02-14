import {IconName} from '@dagster-io/ui-components';

import {assertUnreachable} from '../../app/Util';
import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {isKindTag} from '../../graph/KindTags';
import {weakMapMemoize} from '../../util/weakMapMemoize';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';

export const getAttributesMap = (assets: AssetGraphQueryItem[]) => {
  const assetNamesSet: Set<string> = new Set();
  const tagSet: Set<{key: string; value: string}> = new Set();
  const ownersSet: Set<string> = new Set();
  const groupsSet: Set<string> = new Set();
  const kindsSet: Set<string> = new Set();
  const codeLocationSet: Set<string> = new Set();

  assets.forEach((asset) => {
    assetNamesSet.add(asset.name);
    asset.node.tags.forEach((tag) => {
      if (isKindTag(tag)) {
        return;
      }
      tagSet.add(memoizedTag(tag.key, tag.value));
    });
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
    if (asset.node.groupName) {
      groupsSet.add(asset.node.groupName);
    }
    asset.node.kinds.forEach((kind) => {
      kindsSet.add(kind);
    });
    const location = buildRepoPathForHuman(
      asset.node.repository.name,
      asset.node.repository.location.name,
    );
    codeLocationSet.add(location);
  });

  const assetNames = Array.from(assetNamesSet).sort();
  const tagNames = Array.from(tagSet).sort();
  const owners = Array.from(ownersSet).sort();
  const groups = Array.from(groupsSet).sort();
  const kinds = Array.from(kindsSet).sort();
  const codeLocations = Array.from(codeLocationSet).sort();

  return {
    key: assetNames,
    tag: tagNames,
    owner: owners,
    group: groups,
    kind: kinds,
    code_location: codeLocations,
  };
};

const memoizedTag = weakMapMemoize((key: string, value: string) => ({
  key,
  value,
}));

export type Attribute = keyof ReturnType<typeof getAttributesMap>;

export const attributeToIcon: Record<Attribute, IconName> = {
  key: 'magnify_glass',
  kind: 'compute_kind',
  code_location: 'code_location',
  group: 'asset_group',
  owner: 'owner',
  tag: 'tag',
};

export const assetSelectionSyntaxSupportedAttributes: Attribute[] = Object.keys(
  attributeToIcon,
) as Attribute[];

export const unsupportedAttributeMessages = {
  column_tag: 'column_tag filtering is available in Dagster+',
  column: 'column filtering is available in Dagster+',
  table_name: 'table_name filtering is available in Dagster+',
  changed_in_branch: 'changed_in_branch filtering is available in Dagster+ branch deployments',
};
