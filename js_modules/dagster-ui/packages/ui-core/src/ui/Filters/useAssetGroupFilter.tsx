import {Box, Icon} from '@dagster-io/ui-components';
import {useCallback, useMemo} from 'react';

import {buildAssetGroupSelector} from '../../assets/AssetGroupSuggest';
import {AssetGroupSelector, AssetNode} from '../../graphql/types';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';
import {StaticBaseConfig, useStaticSetFilter} from '../BaseFilters/useStaticSetFilter';

export const useAssetGroupFilter = ({
  allAssetGroups,
  assetGroups,
  setGroups,
}: {
  allAssetGroups?: AssetGroupSelector[] | null;
  assetGroups?: AssetGroupSelector[] | null;
  setGroups?: null | ((groups: AssetGroupSelector[]) => void);
}) => {
  const allValues = useMemo(
    () =>
      (allAssetGroups || []).map((group) => ({
        key: group.groupName,
        value:
          assetGroups?.find(
            (visibleGroup) =>
              visibleGroup.groupName === group.groupName &&
              visibleGroup.repositoryName === group.repositoryName &&
              visibleGroup.repositoryLocationName === group.repositoryLocationName,
          ) ?? group,
        match: [group.groupName],
      })),
    [allAssetGroups, assetGroups],
  );
  return useStaticSetFilter<AssetGroupSelector>({
    ...BaseConfig,
    allValues,
    menuWidth: '300px',
    state: useMemo(() => new Set(assetGroups ?? []), [assetGroups]),
    onStateChanged: useCallback(
      (values: Set<AssetGroupSelector>) => {
        if (setGroups) {
          setGroups(Array.from(values));
        }
      },
      [setGroups],
    ),
  });
};

export function useAssetGroupsForAssets(
  assets: {
    definition?: {
      groupName: string | null;
      repository: Pick<AssetNode['repository'], 'name'> & {
        location: Pick<AssetNode['repository']['location'], 'name'>;
      };
    } | null;
  }[],
) {
  return useMemo(() => {
    return Array.from(
      new Set(
        assets
          .flatMap(({definition}) => (definition ? buildAssetGroupSelector({definition}) : null))
          .filter((o) => o)
          .filter((o, i, arr) => arr.indexOf(o) === i) as AssetGroupSelector[],
      ),
    ).sort((a, b) => a.groupName.localeCompare(b.groupName));
  }, [assets]);
}

const getTooltipText = (group: AssetGroupSelector) =>
  group.groupName +
  ' - ' +
  buildRepoPathForHuman(group.repositoryName, group.repositoryLocationName);

export const BaseConfig: StaticBaseConfig<AssetGroupSelector> = {
  name: 'Asset groups',
  icon: 'asset_group',
  renderLabel: ({value}: {value: AssetGroupSelector}) => (
    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
      <Icon name="repo" />
      <TruncatedTextWithFullTextOnHover
        tooltipText={getTooltipText(value)}
        text={
          <>
            {value.groupName}
            <span style={{opacity: 0.5, paddingLeft: '4px'}}>
              {buildRepoPathForHuman(value.repositoryName, value.repositoryLocationName)}
            </span>
          </>
        }
      />
    </Box>
  ),
  getStringValue: (group) => group.groupName,
  getTooltipText,
};
