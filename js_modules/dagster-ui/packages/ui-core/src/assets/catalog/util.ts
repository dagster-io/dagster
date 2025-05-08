import {useCatalogViews} from 'shared/assets/catalog/useCatalogViews.oss';

import {assertUnreachable} from '../../app/Util';
import {
  linkToAssetTableWithAssetOwnerFilter,
  linkToAssetTableWithGroupFilter,
  linkToAssetTableWithKindFilter,
  linkToAssetTableWithTagFilter,
  linkToCodeLocationInCatalog,
} from '../../search/links';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {AssetTableFragment} from '../types/AssetTableFragment.types';

export type ViewType =
  | ReturnType<typeof useCatalogViews>['privateViews'][number]
  | ReturnType<typeof useCatalogViews>['publicViews'][number];

type GroupedAssets = Record<string, {label: string; assets: AssetTableFragment[]; link: string}>;

export function getGroupedAssets(assets: AssetTableFragment[]) {
  return assets.reduce(
    (acc, asset) => {
      const {definition} = asset;
      if (!definition) {
        return acc;
      }
      const {owners, groupName, repository, tags, kinds} = definition;
      if (owners) {
        owners.forEach((owner) => {
          switch (owner.__typename) {
            case 'TeamAssetOwner':
              acc.owners[owner.team] = acc.owners[owner.team] || {
                assets: [],
                label: owner.team,
                link: linkToAssetTableWithAssetOwnerFilter(owner),
              };
              acc.owners[owner.team]!.assets.push(asset);
              break;
            case 'UserAssetOwner':
              acc.owners[owner.email] = acc.owners[owner.email] || {
                assets: [],
                label: owner.email,
                link: linkToAssetTableWithAssetOwnerFilter(owner),
              };
              acc.owners[owner.email]!.assets.push(asset);
              break;
            default:
              assertUnreachable(owner);
          }
        });
      }
      if (groupName) {
        acc.groupName[groupName] = acc.groupName[groupName] || {
          assets: [],
          label: groupName,
          link: linkToAssetTableWithGroupFilter({
            groupName,
            repositoryLocationName: repository?.location.name,
            repositoryName: repository?.name,
          }),
        };
        acc.groupName[groupName]!.assets.push(asset);
      }
      if (repository) {
        const name = buildRepoPathForHuman(repository.name, repository.location.name);
        acc.repository[name] = acc.repository[name] || {
          assets: [],
          label: name,
          link: linkToCodeLocationInCatalog(repository.name, repository.location.name),
        };
        acc.repository[name]!.assets.push(asset);
      }
      if (tags) {
        tags.forEach((tag) => {
          const stringValue = `${tag.key}${tag.value ? ': ' + tag.value : ''}`;
          acc.tags[stringValue] = acc.tags[stringValue] || {
            assets: [],
            label: stringValue,
            link: linkToAssetTableWithTagFilter(tag),
          };
          acc.tags[stringValue]!.assets.push(asset);
        });
      }
      if (kinds) {
        kinds.forEach((kind) => {
          acc.kinds[kind] = acc.kinds[kind] || {
            assets: [],
            label: kind,
            link: linkToAssetTableWithKindFilter(kind),
          };
          acc.kinds[kind]!.assets.push(asset);
        });
      }
      return acc;
    },
    {
      owners: {} as GroupedAssets,
      groupName: {} as GroupedAssets,
      repository: {} as GroupedAssets,
      tags: {} as GroupedAssets,
      kinds: {} as GroupedAssets,
    },
  );
}
