import {COMMON_COLLATOR} from '../app/Util';
import {AssetTableDefinitionFragment} from '../assets/types/AssetTableFragment.types';
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

type CountPerGroupName = {
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
    'owners' | 'computeKind' | 'groupName' | 'repository'
  > | null;
};

export function buildAssetCountBySection(assets: AssetDefinitionMetadata[]): AssetCountsResult {
  const assetCountByOwner: Record<string, number> = {};
  const assetCountByComputeKind: Record<string, number> = {};
  const assetCountByGroup: Record<string, number> = {};
  const assetCountByCodeLocation: Record<string, number> = {};

  assets
    .filter((asset) => asset.definition)
    .forEach((asset) => {
      const assetDefinition = asset.definition!;
      assetDefinition.owners.forEach((owner) => {
        const ownerKey = owner.__typename === 'UserAssetOwner' ? owner.email : owner.team;
        assetCountByOwner[ownerKey] = (assetCountByOwner[ownerKey] || 0) + 1;
      });

      const computeKind = assetDefinition.computeKind;
      if (computeKind) {
        assetCountByComputeKind[computeKind] = (assetCountByComputeKind[computeKind] || 0) + 1;
      }

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
        assetCountByGroup[groupIdentifier] = (assetCountByGroup[groupIdentifier] || 0) + 1;
      }

      const stringifiedCodeLocation = buildRepoPathForHuman(repositoryName, locationName);
      assetCountByCodeLocation[stringifiedCodeLocation] =
        (assetCountByCodeLocation[stringifiedCodeLocation] || 0) + 1;
    });

  const countsByOwner = Object.entries(assetCountByOwner)
    .map(([owner, count]) => ({
      owner,
      assetCount: count,
    }))
    .sort(({owner: ownerA}, {owner: ownerB}) => COMMON_COLLATOR.compare(ownerA, ownerB));
  const countsByComputeKind = Object.entries(assetCountByComputeKind)
    .map(([computeKind, count]) => ({
      computeKind,
      assetCount: count,
    }))
    .sort(({computeKind: computeKindA}, {computeKind: computeKindB}) =>
      COMMON_COLLATOR.compare(computeKindA, computeKindB),
    );
  const countPerAssetGroup = Object.entries(assetCountByGroup)
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
  const countPerCodeLocation = Object.entries(assetCountByCodeLocation)
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
    countPerAssetGroup,
    countPerCodeLocation,
  };
}
