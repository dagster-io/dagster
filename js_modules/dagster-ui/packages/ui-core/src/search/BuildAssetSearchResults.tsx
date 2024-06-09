import {COMMON_COLLATOR} from '../app/Util';
import {AssetTableDefinitionFragment} from '../assets/types/AssetTableFragment.types';
import {isCanonicalStorageKindTag} from '../graph/KindTags';
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

type CountByComputeKind = {
  computeKind: string;
  assetCount: number;
};

type CountByStorageKind = {
  storageKind: string;
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
  countsByComputeKind: CountByComputeKind[];
  countPerTag: CountPerTag[];
  countPerAssetGroup: CountPerGroupName[];
  countPerCodeLocation: CountPerCodeLocation[];
  countsByStorageKind: CountByStorageKind[];
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
  const assetCountByComputeKind = new CaseInsensitiveCounters();
  const assetCountByStorageKind = new CaseInsensitiveCounters();
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
        assetCountByComputeKind.increment(computeKind);
      }

      assetDefinition.tags.forEach((tag) => {
        if (isCanonicalStorageKindTag(tag)) {
          assetCountByStorageKind.increment(tag.value);
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
  const countsByComputeKind = assetCountByComputeKind
    .entries()
    .map(([computeKind, count]) => ({
      computeKind,
      assetCount: count,
    }))
    .sort(({computeKind: computeKindA}, {computeKind: computeKindB}) =>
      COMMON_COLLATOR.compare(computeKindA, computeKindB),
    );
  const countsByStorageKind = assetCountByStorageKind
    .entries()
    .map(([storageKind, count]) => ({
      storageKind,
      assetCount: count,
    }))
    .sort(({storageKind: storageKindA}, {storageKind: storageKindB}) =>
      COMMON_COLLATOR.compare(storageKindA, storageKindB),
    );

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
    countsByComputeKind,
    countPerTag,
    countPerAssetGroup,
    countPerCodeLocation,
    countsByStorageKind,
  };
}
