import {COMMON_COLLATOR} from '../app/Util';
import {AssetTableDefinitionFragment} from '../assets/types/AssetTableFragment.types';
import {isCanonicalStorageKindTag, isKindTag, KIND_TAG_PREFIX} from '../graph/KindTags';
import {DefinitionTag} from '../graphql/types';
import {buildTagString} from '../ui/tagAsString';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {repoAddressFromPath} from '../workspace/repoAddressFromPath';
import {RepoAddress} from '../workspace/types';

type CountByOwner = {
  owner: string;
  assetCount: number;
};

type CountByKind = {
  kind: string;
  assetCount: number;
};

type CountPerTag = {
  tag: DefinitionTag;
  assetCount: number;
};

export type CountPerGroupName = {
  assetCount: number;
  groupMetadata: GroupMetadata;
};

type CountPerCodeLocation = {
  repoAddress: RepoAddress;
  assetCount: number;
};

type AssetCountsResult = {
  countsByOwner: CountByOwner[];
  countsByKind: CountByKind[];
  countPerTag: CountPerTag[];
  countPerAssetGroup: CountPerGroupName[];
  countPerCodeLocation: CountPerCodeLocation[];
};

export type GroupMetadata = {
  groupName: string;
  repositoryLocationName: string;
  repositoryName: string;
};

type AssetDefinitionMetadata = {
  definition: Pick<
    AssetTableDefinitionFragment,
    'owners' | 'computeKind' | 'groupName' | 'repository' | 'tags'
  > | null;
};

class CaseInsensitiveCounters {
  private _labels: {[key: string]: string} = {};
  private _entries: {[key: string]: number} = {};

  increment(label: string) {
    const labelLower = label.toLowerCase();

    // Allow label containing uppercase letters to overwrite existing label
    if (!this._labels[labelLower] || label !== labelLower) {
      this._labels[labelLower] = label;
    }
    this._entries[labelLower] = (this._entries[labelLower] || 0) + 1;
  }

  entries() {
    return Object.entries(this._entries).map(([k, v]) => [this._labels[k], v] as [string, number]);
  }
}

export function buildAssetCountBySection(assets: AssetDefinitionMetadata[]): AssetCountsResult {
  const assetCountByOwner = new CaseInsensitiveCounters();
  const assetCountByKind = new CaseInsensitiveCounters();
  const assetCountByGroup = new CaseInsensitiveCounters();
  const assetCountByCodeLocation = new CaseInsensitiveCounters();
  const assetCountByTag = new CaseInsensitiveCounters();

  assets
    .filter((asset) => asset.definition)
    .forEach((asset) => {
      const assetDefinition = asset.definition!;
      assetDefinition.owners.forEach((owner) => {
        const ownerKey = owner.__typename === 'UserAssetOwner' ? owner.email : owner.team;
        assetCountByOwner.increment(ownerKey);
      });

      const computeKind = assetDefinition.computeKind;
      if (computeKind) {
        assetCountByKind.increment(computeKind);
      }

      assetDefinition.tags.forEach((tag) => {
        if (isKindTag(tag)) {
          assetCountByKind.increment(tag.key.substring(KIND_TAG_PREFIX.length));
        } else {
          const stringifiedTag = JSON.stringify(tag);
          assetCountByTag.increment(stringifiedTag);
        }
      });

      const groupName = assetDefinition.groupName;
      const locationName = assetDefinition.repository.location.name;
      const repositoryName = assetDefinition.repository.name;

      if (groupName) {
        const metadata: GroupMetadata = {
          groupName,
          repositoryLocationName: locationName,
          repositoryName,
        };
        const groupIdentifier = JSON.stringify(metadata);
        assetCountByGroup.increment(groupIdentifier);
      }

      const stringifiedCodeLocation = buildRepoPathForHuman(repositoryName, locationName);
      assetCountByCodeLocation.increment(stringifiedCodeLocation);
    });

  const countsByOwner = assetCountByOwner
    .entries()
    .map(([owner, count]) => ({
      owner,
      assetCount: count,
    }))
    .sort(({owner: ownerA}, {owner: ownerB}) => COMMON_COLLATOR.compare(ownerA, ownerB));
  const countsByKind = assetCountByKind
    .entries()
    .map(([kind, count]) => ({
      kind,
      assetCount: count,
    }))
    .sort(({kind: kindA}, {kind: kindB}) => COMMON_COLLATOR.compare(kindA, kindB));

  const countPerTag = assetCountByTag
    .entries()
    .map(([tagIdentifier, count]) => ({
      assetCount: count,
      tag: JSON.parse(tagIdentifier),
    }))
    .sort(({tag: TagA}, {tag: TagB}) =>
      COMMON_COLLATOR.compare(
        buildTagString({
          key: TagA.key,
          value: TagA.value,
        }),
        buildTagString({
          key: TagB.key,
          value: TagB.value,
        }),
      ),
    );

  const countPerAssetGroup = assetCountByGroup
    .entries()
    .map(([groupIdentifier, count]) => ({
      assetCount: count,
      groupMetadata: JSON.parse(groupIdentifier),
    }))
    .sort(
      ({groupMetadata: groupMetadataA}, {groupMetadata: groupMetadataB}) =>
        COMMON_COLLATOR.compare(
          repoAddressAsHumanString({
            name: groupMetadataA.repositoryName,
            location: groupMetadataA.repositoryLocationName,
          }),
          repoAddressAsHumanString({
            name: groupMetadataB.repositoryName,
            location: groupMetadataB.repositoryLocationName,
          }),
        ) || COMMON_COLLATOR.compare(groupMetadataA.groupName, groupMetadataB.groupName),
    );
  const countPerCodeLocation = assetCountByCodeLocation
    .entries()
    .map(([key, count]) => ({
      repoAddress: repoAddressFromPath(key)!,
      assetCount: count,
    }))
    .sort(({repoAddress: repoAddressA}, {repoAddress: repoAddressB}) =>
      COMMON_COLLATOR.compare(
        repoAddressAsHumanString(repoAddressA),
        repoAddressAsHumanString(repoAddressB),
      ),
    );

  return {
    countsByOwner,
    countsByKind,
    countPerTag,
    countPerAssetGroup,
    countPerCodeLocation,
  };
}
