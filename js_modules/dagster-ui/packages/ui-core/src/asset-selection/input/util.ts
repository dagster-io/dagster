import {assertUnreachable} from '../../app/Util';
import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {isKindTag} from '../../graph/KindTags';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';

export const getAttributesMap = (assets: AssetGraphQueryItem[]) => {
  const assetNamesSet: Set<string> = new Set();
  const tagNamesSet: Set<string> = new Set();
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
      if (tag.key && tag.value) {
        // We add quotes around the equal sign here because the auto-complete suggestion already wraps the entire value in quotes.
        // So wer end up with tag:"key"="value" as the final suggestion
        tagNamesSet.add(`${tag.key}"="${tag.value}`);
      } else {
        tagNamesSet.add(tag.key);
      }
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
  const tagNames = Array.from(tagNamesSet).sort();
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
